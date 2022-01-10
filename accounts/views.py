import random
from itertools import chain

import requests
from django.contrib.auth import login, logout
from django.contrib.auth.models import update_last_login
from django.core.mail import EmailMultiAlternatives, get_connection, send_mail
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_redis import get_redis_connection
from rest_framework import exceptions, status
from rest_framework import filters
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User, Follow
from actions.models import Action
from actions.serializers import ActionSerializer
from core import settings
from other.models import RegisterSecretCode
from other.permissions import IsAnonymous
from other.utils import get_client_ip
from other.validators import validate_email
from .serializers import UserRegisterSerializer, PasswordChangeSerializer, UserSerializer, UserPasswordReset

# from django_filters import rest_framework as df_filters

r = get_redis_connection("default")


class UsersActionsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        following_brand_ids = user.followings_brand.values_list('id', flat=True)
        new_actions = Action.objects.filter(brand__id__in=following_brand_ids, seen=False) \
            .select_related('brand') \
            .prefetch_related('target').order_by('created_at')
        seen_actions = Action.objects.filter(brand__id__in=following_brand_ids, seen=True) \
                           .select_related('brand') \
                           .prefetch_related('target').order_by('created_at')[:10]
        actions = list(chain(new_actions, seen_actions))
        serializer = ActionSerializer(actions, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class UserFollowListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, follow):
        user = self.request.user
        fields = ['uuid', 'username', 'slug', 'picture', 'first_name', 'last_name',
                  'short_bio', 'is_official', 'followers_count']
        if follow == 'followers':
            followers = User.objects.filter(followings_user=user, rel_from_user__status=True)
            serializer = UserSerializer(followers, fields=fields, many=True, context={"fields": fields})
            return Response({
                'status': True,
                'data': serializer.data,
                'data_length': len(serializer.data),
            }, status=status.HTTP_200_OK)
        elif follow == 'followings':
            followings = User.objects.filter(followers=user, rel_to_user__status=True)
            serializer = UserSerializer(followings, fields=fields, many=True, context={"fields": fields})
            return Response({
                'status': True,
                'data': serializer.data,
                'data_length': len(serializer.data),
            }, status=status.HTTP_200_OK)


class UserFollowAcceptAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        from_user = get_object_or_404(User, is_active=True, username=username)
        to_user = self.request.user
        follow_request = get_object_or_404(Follow, from_user=from_user, to_user=to_user, status=False)
        follow_request.status = True
        follow_request.allowed_at = timezone.now()
        follow_request.save()
        return Response({
            'status': True
        }, status=status.HTTP_202_ACCEPTED)


class UserFollowActionAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username, action):
        from_user = self.request.user
        to_user = get_object_or_404(User, is_active=True, username=username)
        if from_user == to_user:
            raise exceptions.ValidationError({'detail': _('You can not follow to self :) BAD BOY!')})
        if action == 'follow':
            if Follow.objects.filter(from_user=from_user, to_user=to_user, status=True).exists():
                return Response({
                    'success': False,
                    'detail': _(f"You already following to '{to_user}'.")
                }, status=status.HTTP_400_BAD_REQUEST)
            elif to_user.is_private:
                if Follow.objects.filter(from_user=from_user, to_user=to_user, status=False).exists():
                    return Response({
                        'success': False,
                        'detail': _(f"You already requested to '{to_user}'.")
                    }, status=status.HTTP_400_BAD_REQUEST)
                Follow.objects.create(from_user=from_user, to_user=to_user)
                return Response({
                    'success': True,
                    'detail': _(f"Request for following sent to '{to_user}'.")
                }, status=status.HTTP_200_OK)
            Follow.objects.create(from_user=from_user, to_user=to_user,
                                  status=True, allowed_at=timezone.now())
            return Response({
                'success': True,
                'detail': _(f"You following to '{to_user}'.")
            }, status=status.HTTP_200_OK)
        elif action == 'unfollow':
            if Follow.objects.filter(from_user=from_user, to_user=to_user, status=True).exists():
                follow = Follow.objects.get(from_user=from_user, to_user=to_user, status=True)
                follow.delete()
                return Response({
                    'success': True,
                    'detail': _(f"You unfollowed from '{to_user}'.")
                }, status=status.HTTP_200_OK)
            elif Follow.objects.filter(from_user=from_user, to_user=to_user, status=False).exists():
                follow = Follow.objects.get(from_user=from_user, to_user=to_user, status=False)
                follow.delete()
                return Response({
                    'success': True,
                    'detail': _(f"Request removed from '{to_user}'.")
                }, status=status.HTTP_200_OK)
            return Response({
                'success': False,
                'detail': _(f"You not following to '{to_user}'.")
            }, status=status.HTTP_400_BAD_REQUEST)
        raise exceptions.ValidationError({'detail': _('Wrong action request.')})


class UserSearchAPI(APIView):
    class CustomSearchFilter(filters.SearchFilter):
        search_param = 'u'

        def get_search_terms(self, request):
            params = request.query_params.get(self.search_param, '')
            check_params = params.replace(' ', '')
            if len(check_params) < 3:
                raise exceptions.ValidationError({'detail': _('Minimum search character is 3.')})
            params = params.replace('\x00', '')  # strip null characters
            params = params.replace(',', ' ')
            return params.split()

    filter_backends = [CustomSearchFilter]
    search_fields = ['username']

    def get(self, request):
        fields = ['uuid', 'username', 'slug', 'picture', 'first_name', 'last_name',
                  'short_bio', 'is_official', 'followers_count']
        users = User.objects.filter(is_active=True)
        for backend in list(self.filter_backends):
            users = backend().filter_queryset(self.request, users, self)
        serializer = UserSerializer(users, many=True, fields=fields)
        return Response({
            'success': True,
            'data': serializer.data,
            'data_length': len(serializer.data),
        })


class MeDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        fields = ['uuid', 'username', 'slug', 'birth_date', 'picture', 'first_name', 'last_name', 'phone_number',
                  'gender',
                  'about_me', 'short_bio', 'email', 'city', 'is_verified', 'is_official', 'account_views', 'address',
                  'is_private', 'receive_sms', 'followers_count', 'followings_count_user', 'followings_count_brand']
        serializer = UserSerializer(user, fields=fields, context={'fields': fields})
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request):
        user = self.request.user
        fields = ['username', 'picture', 'first_name', 'last_name',
                  'birth_date', 'address', 'city', 'gender', 'receive_sms', 'geolocation',
                  'about_me', 'short_bio', 'is_private']
        serializer = UserSerializer(user, data=request.data, fields=fields)
        city = request.data.get('city', None)
        if serializer.is_valid():
            serializer.save(city=city)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = self.request.user
        user.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)


class UserDetailAPI(APIView):

    def get(self, request, username):
        if username is not None:
            user = get_object_or_404(User, is_active=True, username__iexact=username)
        else:
            raise exceptions.NotFound(_("User with that name not found."))
        fields = ['username', 'slug', 'picture', 'first_name', 'last_name',
                  'about_me', 'short_bio', 'is_verified', 'is_official',
                  'is_private', 'followers_count', 'followings_count_user', 'followings_count_brand']
        serializer = UserSerializer(user, fields=fields, context={'fields': fields})
        # Unique ip views
        ip = get_client_ip(request)
        r.zincrby(f"user:views:{user.pk}", 1, ip)
        data = {
            'success': True,
            'data': serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)


class PasswordChangeAPI(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def put(request):
        user = request.user
        serializer = PasswordChangeSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPI(APIView):

    @staticmethod
    def post(request):
        response = Response()
        # Clear Browser Header
        response['Authorization'] = ''
        # response.delete_cookie(key='jwt')
        # response.delete_cookie(key='rt')
        logout(request)
        return Response({
            'success': True
        }, status=status.HTTP_200_OK)


class LoginAPI(APIView):
    permission_classes = [IsAnonymous]

    @staticmethod
    def post(request):
        if request.data.get('login', None) is None or request.data.get('password', None) is None:
            return Response({
                'success': False,
                'errors': _('Fill both login and password fields!')
            }, status=status.HTTP_400_BAD_REQUEST)

        login_ = request.data['login']
        password = request.data['password']
        remember = request.data.get('remember_me', None)

        email, user_name, phone_number = False, False, False
        # Define username or email
        if '+' in login_ or login_.isdigit():
            phone_number = str(login_)
        elif '@' in login_:
            email = str(login_)
        else:
            user_name = str(login_)
        # Get user by username or email or phone_number
        try:
            if email:
                user = User.objects.get(email__iexact=email)
            elif phone_number:
                strict_number = phone_number.replace(' ', '').replace('-', '')[-9:]
                user = User.objects.get(phone_number=strict_number)
            elif user_name:
                user = User.objects.get(username__iexact=user_name)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Incorrect input credentials!'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            raise exceptions.AuthenticationFailed({'detail': Exception})
        # Check user password
        if not user.check_password(password):
            return Response({
                'success': False,
                'error': 'Incorrect input credentials!'
            }, status=status.HTTP_401_UNAUTHORIZED)
        # Create Token for user
        refresh = RefreshToken.for_user(user)
        login(request, user)
        update_last_login(None, user)
        if remember:
            pass  # do something
        return Response({
            'success': True,
            'token': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_200_OK)


class RegisterUserAPI(APIView):
    permission_classes = [IsAnonymous]

    @staticmethod
    def post(request, phone_or_email):
        secret_code = request.data.get('secret_code', None)
        if not secret_code:
            raise exceptions.ValidationError({'errors': {'secret_code': _('Type secret code')}})
        get_model = RegisterSecretCode.objects.filter(phone_or_email=phone_or_email, secret_code=secret_code,
                                                      type='user').first()
        if not get_model:
            raise exceptions.ValidationError({'errors': {'secret_code': _('Incorrect secret code')}})
        data = {'username': get_model.username,
                'phone_or_email': get_model.phone_or_email,
                'password': get_model.password}
        serializer = UserRegisterSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            login(request, user)
            update_last_login(None, user)
            get_model.delete()
            return Response({
                'success': True,
                'token': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ValidateSendRegister(APIView):
    permission_classes = [IsAnonymous]

    @staticmethod
    def post(request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            secret_code = str(random.random())[-6:]
            phone_or_email = serializer.data.get('phone_or_email', None)
            if '@' in phone_or_email:
                subject, from_email, to = 'Код подтверждения', 'imager - Код подтверждения <imager@umail.uz>', phone_or_email
                text_content = f'Код для подтверждения регистрации: {secret_code}'
                html_content = f'Код для подтверждения регистрации: \n<strong>{secret_code}</strong>'
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                # send_mail(subject, text_content, from_email, [to])
            else:
                payload = {'mobile_phone': f"998{phone_or_email}",
                           'message': f"#imager - Имя аккаунта: {serializer.data['username']}\n"
                                      f'Код подтверждения:  {secret_code}',
                           'from': '4546',
                           'callback_url': 'https://imager.uz/sms.html'}
                response = requests.request("POST", settings.SMS_url, headers=settings.SMS_headers, data=payload)
                print(response.text)

            get_model = RegisterSecretCode.objects.filter(phone_or_email=serializer.data['phone_or_email'])
            if get_model:
                for model in get_model:
                    model.delete()
            RegisterSecretCode.objects.create(secret_code=secret_code,
                                              phone_or_email=serializer.data['phone_or_email'],
                                              username=serializer.data['username'],
                                              password=request.data['password'],
                                              type='user')
            return Response({
                'success': True,
                'data': {
                    'redirect': True,
                    'phone_or_email': serializer.data['phone_or_email'],
                }
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ValidateResendRegister(APIView):
    permission_classes = [IsAnonymous]

    @staticmethod
    def post(request, phone_or_email):
        model = RegisterSecretCode.objects.filter(phone_or_email=phone_or_email).first()
        if not model:
            raise exceptions.ValidationError(_("Incorrect phone number or email. Try again."))
        secret_code = str(random.random())[-6:]
        if '@' in phone_or_email:
            subject, from_email, to = 'Код подтверждения', 'imager - Код подтверждения <imager@umail.uz>', phone_or_email
            text_content = f'Код для подтверждения регистрации: \n{secret_code}'
            html_content = f'Код для подтверждения регистрации: \n<strong>{secret_code}</strong>'
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        else:
            payload = {'mobile_phone': f"998{phone_or_email}",
                       'message': f'#imager - Имя аккаунта: {model.username}\n'
                                  f'Код подтверждения:  {secret_code}',
                       'from': '4546',
                       'callback_url': 'https://imager.uz/sms.html'}
            response = requests.request("POST", settings.SMS_url, headers=settings.SMS_headers, data=payload)
            print(response.text)

        RegisterSecretCode.objects.create(secret_code=secret_code,
                                          phone_or_email=phone_or_email,
                                          username=model.username,
                                          password=model.password)
        model.delete()

        return Response({
            'success': True,
            'data': {
                'redirect': True,
                'phone_or_email': phone_or_email,
            }
        }, status=status.HTTP_200_OK)


class ResetPasswordValidate(APIView):

    @staticmethod
    def post(request):
        phone_or_email = request.data.get('phone_or_email', None)
        if not phone_or_email:
            return Response({
                'success': False,
                'error': {"phone_or_email": _('This field is required')}
            }, status=status.HTTP_401_UNAUTHORIZED)
        email, phone, user = False, False, False
        if '@' in phone_or_email:
            validate_email(phone_or_email)
            email = phone_or_email
        else:
            strict_number = phone_or_email.replace(' ', '').replace('-', '')[-9:]
            if not strict_number.isdigit() or len(strict_number) < 9:
                raise exceptions.ValidationError(_('Input valid phone number or email'))
            phone = strict_number
            phone_or_email = strict_number
        try:
            if email:
                user = User.objects.get(email__iexact=email)
            elif phone:
                user = User.objects.get(phone_number=phone)
        except:
            return Response({
                'success': False,
                'error': {"not_found": _('User with that data not found')}
            }, status=status.HTTP_401_UNAUTHORIZED)
        secret_code = str(random.random())[-6:]
        if email:
            subject, from_email, to = 'Код для восстановления пароля', 'imager - Код восстановления <imager@umail.uz>', email
            text_content = f'Код для восстановления пароля: \n{secret_code}'
            html_content = f'Код для восстановления пароля: \n<strong>{secret_code}</strong>'
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        elif phone:
            payload = {'mobile_phone': f"998{phone}",
                       'message': f'#imager - Имя аккаунта: {user.username}\n'
                                  f'Код восстановления:  {secret_code}',
                       'from': '4546',
                       'callback_url': 'https://imager.uz/sms.html'}
            response = requests.request("POST", settings.SMS_url, headers=settings.SMS_headers, data=payload)
            print(response.text)
        else:
            return Response({
                'success': False,
                'error': {"error": _('Something went wrong, try again')}
            }, status=status.HTTP_401_UNAUTHORIZED)

        get_model = RegisterSecretCode.objects.filter(phone_or_email=phone_or_email)
        if get_model:
            for model in get_model:
                model.delete()

        RegisterSecretCode.objects.create(secret_code=secret_code,
                                          phone_or_email=phone,
                                          username=user.username,
                                          type='user')
        return Response({
            'success': True,
            'data': {
                'redirect': True,
                'phone_or_email': phone_or_email,
            }
        }, status=status.HTTP_200_OK)


class PasswordResetResendRegister(APIView):
    permission_classes = [IsAnonymous]

    @staticmethod
    def post(request, phone_or_email):
        model = RegisterSecretCode.objects.filter(phone_or_email=phone_or_email).first()
        if not model:
            raise exceptions.ValidationError(_("Incorrect phone number or email, try again"))
        email, phone, user = False, False, False
        if '@' in phone_or_email:
            validate_email(phone_or_email)
            email = phone_or_email
        else:
            strict_number = phone_or_email.replace(' ', '').replace('-', '')[-9:]
            if not strict_number.isdigit() or len(strict_number) < 9:
                raise exceptions.ValidationError(_('Input valid phone number or email'))
            phone = strict_number
            phone_or_email = strict_number
        try:
            if email:
                user = User.objects.get(email__iexact=email)
            elif phone:
                user = User.objects.get(phone_number=phone)
        except:
            return Response({
                'success': False,
                'error': {"not_found": _('User with that data not found')}
            }, status=status.HTTP_401_UNAUTHORIZED)
        secret_code = str(random.random())[-6:]
        if email:
            subject, from_email, to = 'Код для восстановления пароля', 'imager - Код восстановления <imager@umail.uz>', email
            text_content = f'Код для восстановления пароля: \n{secret_code}'
            html_content = f'Код для восстановления пароля: \n<strong>{secret_code}</strong>'
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        elif phone:
            payload = {'mobile_phone': f"998{phone}",
                       'message': f'#imager - Имя аккаунта: {user.username}\n'
                                  f'Код восстановления:  {secret_code}',
                       'from': '4546',
                       'callback_url': 'https://imager.uz/sms.html'}
            response = requests.request("POST", settings.SMS_url, headers=settings.SMS_headers, data=payload)
            print(response.text)

        model.delete()
        RegisterSecretCode.objects.create(secret_code=secret_code,
                                          phone_or_email=phone,
                                          username=user.username,
                                          type='user')
        return Response({
            'success': True,
            'data': {
                'redirect': True,
                'phone_or_email': phone_or_email,
            }
        }, status=status.HTTP_200_OK)


class ResetPasswordCode(APIView):

    @staticmethod
    def post(request, phone_or_email):
        secret_code = request.data.get('secret_code', None)
        if not secret_code:
            raise exceptions.ValidationError(_('Type secret code'))
        get_model = RegisterSecretCode.objects.filter(phone_or_email=phone_or_email, secret_code=secret_code,
                                                      type='user').first()
        if not get_model:
            raise exceptions.ValidationError(_('Incorrect secret code'))
        user = get_object_or_404(User, username__iexact=get_model.username)
        get_model.delete()
        return Response({
            'success': True,
            'data': {
                'redirect': True,
                'uuid': user.uuid,
            }
        }, status=status.HTTP_200_OK)


class ResetPassword(APIView):

    @staticmethod
    def post(request, uuid):
        serializer = UserPasswordReset(data=request.data)
        get_user = User.objects.filter(uuid=uuid).first()
        if not get_user:
            raise exceptions.ValidationError(_('User not found'))
        if serializer.is_valid():
            password = request.data.get('password1')
            print(password)
            get_user.set_password(password)
            get_user.save()
            return Response({
                'success': True
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
