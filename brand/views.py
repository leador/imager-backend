import random
import requests

from core import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.settings import MAXIMUM_BRAND_CATEGORIES
from other.models import RegisterSecretCode
from .models import Brand, BrandUser, Contact, OwnCategory, BrandCustomerContacts
from .serializers import \
    BrandRegisterSerializer, \
    BrandSerializer, \
    BrandUserSerializer, \
    BrandUserCreateSerializer, \
    OwnCategoryCreateSerializer, \
    OwnCategorySerializer, BrandContactSerializer


class BrandSearchListAPI(APIView):

    @staticmethod
    def get(request):
        fields = ['name', 'suffix', 'logo', 'rating', 'slug', 'slogan', 'followers_count']
        if not request.query_params or len(request.query_params.get('q')) <= 2:
            raise exceptions.NotFound()
        query = request.query_params.get('q')
        brands = Brand.objects.filter(
            Q(is_active=True) |
            Q(name__icontains=query) |
            Q(suffix__icontains=query) |
            Q(slogan__icontains=query))
        serializer = BrandSerializer(brands, many=True, fields=fields, context={'fields': fields})
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class BrandListAPI(APIView):

    @staticmethod
    def get(request):
        brand = Brand.objects.filter(is_active=True, status=True)
        fields = ['name', 'suffix', 'slug', 'logo', 'rating', 'slogan', 'verified', 'followers_count']
        serializer = BrandSerializer(brand, many=True, fields=fields, context={'fields': fields})
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class BrandDetailAPI(APIView):

    @staticmethod
    def get(request, brand_slug):
        user = request.user
        brand = get_object_or_404(Brand, is_active=True, status=True, slug=brand_slug)
        fields = ['name', 'email', 'suffix', 'slug', 'info', 'followers_count', 'contacts',
                  'slogan', 'rating', 'logo', 'poster', 'address', 'user_followed',
                  'cities', 'delivery', 'geolocation']
        serializer = BrandSerializer(brand, fields=fields, context={'fields': fields})
        data = serializer.data
        data['user_followed'] = True if user in brand.followers.all() else False
        return Response({
            'success': True,
            'data': data
        }, status=status.HTTP_200_OK)


class BrandContactDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, contact):
        user = self.request.user
        try:
            brand_pk = user.brand_user.brand.pk
        except:
            raise exceptions.NotFound()
        brand = get_object_or_404(Brand, is_active=True, pk=brand_pk)
        brand_user = user.brand_user
        if brand_user.is_manager:
            contact_model = BrandCustomerContacts.objects.filter(brand=brand, contact=contact).first()
            contact_model.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)


class BrandRegisterAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, phone_number):
        secret_code = request.data.get('secret_code', None)
        if not secret_code:
            raise exceptions.ValidationError({'errors': {'secret_code': _('Type secret code')}})
        get_model = RegisterSecretCode.objects.filter(phone_or_email=phone_number, type='brand',
                                                      secret_code=secret_code).first()
        if not get_model:
            raise exceptions.ValidationError({'errors': {'secret_code': _('Incorrect secret code')}})
        data = {'name': get_model.title,
                'phone_number': get_model.phone_or_email}
        fields = ['name', 'phone_number']
        serializer = BrandRegisterSerializer(data=data, fields=fields)
        if serializer.is_valid():
            serializer.save(owner=self.request.user)
            get_model.delete()
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ValidateBrandRegisterAPI(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request):
        try:
            brand_user = request.user.brand_user
            return Response({
                'success': False,
                'detail': _(f"You have already exists in brand '{brand_user.brand}'")
            }, status=status.HTTP_400_BAD_REQUEST)
        except BrandUser.DoesNotExist:
            fields = ['name', 'phone_number']
            serializer = BrandRegisterSerializer(data=request.data, fields=fields)
            if serializer.is_valid():
                phone_number = serializer.data.get('phone_number')
                secret_code = str(random.random())[-6:]
                payload = {'mobile_phone': f"998{phone_number}",
                           'message': f"#imager - Имя бренда: {serializer.data['name']}\n"
                                      f'Код для регистрации бренда:  {secret_code}',
                           'from': '4546',
                           'callback_url': 'https://imager.uz/sms.html'}
                response = requests.request("POST", settings.SMS_url, headers=settings.SMS_headers, data=payload)
                print(response.text)

                get_model = RegisterSecretCode.objects.filter(phone_or_email=phone_number)
                if get_model:
                    for model in get_model:
                        model.delete()
                RegisterSecretCode.objects.create(secret_code=secret_code,
                                                  phone_or_email=phone_number,
                                                  title=serializer.data['name'],
                                                  type='brand')
                return Response({
                    'success': True,
                    'data': {
                        'redirect': True,
                        'phone_number': phone_number,
                    }
                }, status=status.HTTP_200_OK)
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)


class ValidateResendBrandRegisterAPI(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, phone_number):
        model = RegisterSecretCode.objects.filter(phone_or_email=phone_number, type='brand').first()
        if not model:
            raise exceptions.ValidationError(_('Incorrect phone number. Try again'))
        phone_number = model.phone_or_email
        secret_code = str(random.random())[-6:]
        payload = {'mobile_phone': f"998{phone_number}",
                   'message': f"#imager - Имя бренда: {model.title}\n"
                              f'Код для регистрации бренда:  {secret_code}',
                   'from': '4546',
                   'callback_url': 'https://imager.uz/sms.html'}
        response = requests.request("POST", settings.SMS_url, headers=settings.SMS_headers, data=payload)
        print(response.text)

        RegisterSecretCode.objects.create(secret_code=secret_code,
                                          phone_or_email=phone_number,
                                          title=model.title,
                                          type='brand')
        model.delete()
        return Response({
            'success': True,
            'data': {
                'redirect': True,
                'phone_number': phone_number,
            }
        }, status=status.HTTP_200_OK)


class MyBrandAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        try:
            brand_pk = user.brand_user.brand.pk
        except Exception:
            raise exceptions.NotFound()
        brand = get_object_or_404(Brand, is_active=True, pk=brand_pk)
        brand_user = user.brand_user
        if brand_user.is_manager:
            fields = ['owner', 'name', 'email', 'phone_number', 'suffix', 'contacts',
                      'slug', 'info', 'slogan', 'rating', 'logo', 'poster', 'delivery',
                      'status', 'address', 'cities', 'geolocation', 'created_at', 'followers_count']
            serializer = BrandSerializer(brand, fields=fields, context={'fields': fields})
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            raise exceptions.NotFound()

    def put(self, request):
        user = self.request.user
        try:
            brand_pk = user.brand_user.brand.pk
        except Exception:
            raise exceptions.NotFound()
        brand = get_object_or_404(Brand, is_active=True, pk=brand_pk)
        brand_user = user.brand_user
        if brand_user.is_manager:
            fields = ['name', 'email', 'phone_number', 'suffix', 'contacts',
                      'info', 'slogan', 'logo', 'poster', 'delivery',
                      'status', 'address', 'cities', 'geolocation']
            print(request.data)

            _mutable = request.data._mutable
            request.data._mutable = True
            contacts = request.data.pop('contacts', None)
            request.data._mutable = _mutable

            serializer = BrandSerializer(brand, data=request.data, fields=fields, context={'fields': fields})
            if serializer.is_valid():
                if contacts is not None:
                    contacts = contacts[0].split(',')
                    brand_contacts = BrandCustomerContacts.objects.filter(brand=brand)
                    if len(brand_contacts) + len(contacts) > 3:
                        raise exceptions.ValidationError({'errors': {'contacts': _('You have more than 3 contacts. Remove other contact to add new')}})
                    for contact in contacts:
                        strict_number = contact.replace(' ', '')[-9:]
                        if not strict_number.isdigit() or len(strict_number) < 9:
                            raise exceptions.ValidationError({'errors': {'contacts': _('Input full valid phone numbers with 9 digits')}})
                        BrandCustomerContacts.objects.create(brand=brand, contact=strict_number)
                serializer.save()
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise exceptions.NotFound()

    def delete(self, request):
        user = self.request.user
        try:
            brand_pk = user.brand.pk
        except Exception:
            raise exceptions.NotFound()
        brand = get_object_or_404(Brand, is_active=True, pk=brand_pk)
        if user == brand.owner:
            brand.delete()
            return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
        else:
            raise exceptions.NotFound()


class UserFollowingAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, brand_slug, action):
        brand = get_object_or_404(Brand, is_active=True, status=True, slug=brand_slug)
        user = self.request.user
        if user not in brand.followers.all() and action == 'follow':
            Contact.objects.create(from_user=user, to_brand=brand)
            return Response({'success': True}, status=status.HTTP_200_OK)
        elif user in brand.followers.all() and action == 'unfollow':
            follow = Contact.objects.get(from_user=user, to_brand=brand)
            follow.delete()
            return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
        else:
            raise exceptions.ValidationError({'detail': _('You already followed or unfollowed.')})


class BrandMembersListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, brand_slug):
        brand = get_object_or_404(Brand, is_active=True, slug=brand_slug)
        user = self.request.user
        try:
            if brand == user.brand_user.brand and user.brand_user.is_manager:
                brand_members = brand.brand_user.all()
                fields = ['user', 'is_manager']
                serializer = BrandUserSerializer(brand_members, many=True, fields=fields)
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
        except BrandUser.DoesNotExist:
            pass
        raise exceptions.NotFound()

    def post(self, request, brand_slug):
        brand = get_object_or_404(Brand, is_active=True, slug=brand_slug)
        user = self.request.user
        try:
            if brand == user.brand_user.brand and user.brand_user.is_manager:
                serializer = BrandUserCreateSerializer(data=request.data)
                username = request.data.get('user')
                member_user = get_object_or_404(get_user_model(), is_active=True, username__iexact=username)
                try:
                    if member_user.brand_user:
                        raise exceptions.ValidationError({'detail': f"User '{username}' is already exists in brand!"})
                except BrandUser.DoesNotExist:
                    if serializer.is_valid():
                        if brand.owner == user:
                            serializer.save(brand=brand, user=member_user)
                        else:
                            serializer.save(brand=brand, user=member_user, is_manager=False)
                        return Response({
                            'success': True,
                            'data': serializer.data
                        }, status=status.HTTP_200_OK)
                    return Response({
                        'success': False,
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                raise exceptions.NotFound()
        except Exception:
            raise exceptions.NotFound()


class BrandMemberDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, brand_slug, member):
        brand = get_object_or_404(Brand, is_active=True, slug=brand_slug)
        user = self.request.user
        try:
            if brand == user.brand_user.brand and user.brand_user.is_manager:
                brand_member = get_object_or_404(BrandUser, user__username__iexact=member, brand=brand)
                fields = ['user', 'is_manager']
                serializer = BrandUserSerializer(brand_member, fields=fields)
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
        except BrandUser.DoesNotExist:
            pass
        raise exceptions.NotFound()

    def put(self, request, brand_slug, member):
        brand = get_object_or_404(Brand, is_active=True, slug=brand_slug)
        user = self.request.user
        if brand.owner == user:
            member = get_object_or_404(BrandUser, user__username__iexact=member, brand=brand)
            serializer = BrandUserSerializer(member, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        raise exceptions.NotFound()

    def delete(self, request, brand_slug, member):
        brand = get_object_or_404(Brand, is_active=True, slug=brand_slug)
        user = self.request.user
        brand_member = get_object_or_404(BrandUser, user__username__iexact=member, brand=brand)
        try:
            if brand.owner == user and not brand_member.user == user:
                brand_member.delete()
                return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
            elif brand == user.brand_user.brand and user.brand_user.is_manager and not brand_member.is_manager:
                brand_member.delete()
                return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
            elif brand == user.brand_user.brand and user.brand_user.is_manager and brand_member.user == user and \
                    not brand.owner == user:
                brand_member.delete()
                return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
            elif brand.owner == user and brand_member.user == user:
                return Response({
                    'success': False,
                    'detail': _('You firstly must give owner status to one of your managers.')
                }, status=status.HTTP_423_LOCKED)
        except BrandUser.DoesNotExist:
            pass
        raise exceptions.NotFound()


class BrandSetOwnerAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, brand_slug, member):
        brand = get_object_or_404(Brand, is_active=True, slug=brand_slug)
        user = self.request.user
        if brand.owner == user:
            brand_member = get_object_or_404(BrandUser, user__username__iexact=member, brand=brand, is_manager=True)
            brand.owner = brand_member.user
            brand.save()
            return Response({'success': True}, status=status.HTTP_200_OK)
        raise exceptions.NotFound()


class OwnCategoryListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, brand_slug):
        brand = get_object_or_404(Brand, is_active=True, slug=brand_slug)
        user = self.request.user
        categories = OwnCategory.objects.filter(brand=brand)
        try:
            if brand == user.brand_user.brand:
                if not categories.exists():
                    return Response({
                        'success': False,
                        'detail': _('Categories not created yet.')
                    }, status=status.HTTP_204_NO_CONTENT)
                fields = ['name', 'brand', 'description', 'slug', 'order', 'uuid']
                serializer = OwnCategorySerializer(categories, many=True, fields=fields)
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            raise exceptions.NotFound()
        except Exception:
            raise exceptions.NotFound()

    def post(self, request, brand_slug):
        brand = get_object_or_404(Brand, is_active=True, slug=brand_slug)
        user = self.request.user
        try:
            if brand == user.brand_user.brand and user.brand_user.is_manager:
                category_count = OwnCategory.objects.filter(brand=brand).count()
                # Validation
                if category_count >= MAXIMUM_BRAND_CATEGORIES:
                    return Response({
                        'success': False,
                        'errors': {"category_limit": _(f"Maximum categories for each brand is {MAXIMUM_BRAND_CATEGORIES}. Remove unused categories.")},
                    }, status=status.HTTP_400_BAD_REQUEST)
                if OwnCategory.objects.filter(brand=brand, name=request.data.get('name')).exists():
                    return Response({
                        'success': False,
                        'errors': {"name": _(f"This name is already exists in your category. Choose another.")},
                    }, status=status.HTTP_400_BAD_REQUEST)

                fields = ['name', 'brand', 'description', 'order', 'uuid']
                serializer = OwnCategoryCreateSerializer(data=request.data, fields=fields)
                if serializer.is_valid():
                    serializer.save(brand=brand)
                    return Response({
                        'success': True,
                        'data': serializer.data
                    }, status=status.HTTP_200_OK)
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            raise exceptions.NotFound()
        except Exception:
            raise exceptions.NotFound()


class OwnCategoryDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, brand_slug, uuid):
        brand = get_object_or_404(Brand, is_active=True, slug=brand_slug)
        user = self.request.user
        category = get_object_or_404(OwnCategory, brand=brand, uuid=uuid)
        try:
            if brand == user.brand_user.brand and user.brand_user.is_manager:
                fields = ['name', 'brand', 'description', 'order', 'uuid']
                serializer = OwnCategorySerializer(category, data=request.data, fields=fields)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'success': True,
                        'data': serializer.data
                    }, status=status.HTTP_200_OK)
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            raise exceptions.NotFound()

    def delete(self, request, brand_slug, uuid):
        brand = get_object_or_404(Brand, is_active=True, slug=brand_slug)
        user = self.request.user
        category = get_object_or_404(OwnCategory, brand=brand, uuid=uuid)
        try:
            if category.slug == 'other':
                return Response({
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)
            if brand == user.brand_user.brand and user.brand_user.is_manager:
                category.delete()
                return Response({
                    'success': True
                }, status=status.HTTP_204_NO_CONTENT)
            raise exceptions.NotFound()
        except Exception:
            raise exceptions.NotFound()
