from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from django_redis import get_redis_connection

from other.serializers import CitySerializer
from other.utils import city_get, city_none_get_or_create
from other.validators import \
    PhoneNumberValidator, \
    MINIMUM_BIRTH_YEAR, \
    MAXIMUM_BIRTH_YEAR, \
    GeoLocationValidator, UsernameValidator, validate_email
from accounts.models import User
from other.choices import Gender
from brand.serializers import BrandSerializer

pass_min_length = 6
r = get_redis_connection("default")


class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault('style', {})

        kwargs['style']['input_type'] = 'password'
        kwargs['write_only'] = True

        super().__init__(**kwargs)


class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(min_length=4, max_length=30, required=True, validators=[UsernameValidator])
    phone_or_email = serializers.CharField(max_length=50, required=True)
    password = PasswordField(max_length=64, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'phone_or_email']

    @staticmethod
    def validate_password(password):
        if len(password) < pass_min_length:
            raise serializers.ValidationError(_(f"Password must contain at least {pass_min_length} characters."))
        return password

    @staticmethod
    def validate_phone_or_email(data):
        if '@' in data:
            validate_email(data)
            if User.objects.filter(Q(email__iexact=data)).exists():
                raise serializers.ValidationError(_('User with that email already exists'))
            return data
        else:
            strict_number = data.replace(' ', '').replace('-', '')[-9:]
            if not strict_number.isdigit() or len(strict_number) < 9:
                raise serializers.ValidationError(_('Input valid phone number or email'))
            if User.objects.filter(Q(phone_number=strict_number)).exists():
                raise serializers.ValidationError(_('User with that phone number already exists'))
            return strict_number

    @staticmethod
    def validate_username(username):
        if username.isdigit():
            raise serializers.ValidationError(_('Only numbers in username not recommended. Type real username, include minimum 1 letter.'))
        if User.objects.filter(Q(username__iexact=username)).exists():
            raise serializers.ValidationError(_('User with that username is already exists.'))
        return username

    def create(self, validated_data):
        phone_or_email = validated_data.get('phone_or_email')
        email, phone_number = False, False
        if '@' in phone_or_email:
            email = phone_or_email
        else:
            phone_number = phone_or_email
        username = validated_data.get('username')
        password = validated_data.get('password')
        if email:
            user = User.objects.create(username=username, email=email)
        else:
            user = User.objects.create(username=username, phone_number=phone_number)
        user.city = city_none_get_or_create()
        if password is not None:
            user.set_password(password)
        user.save()
        return user


class PasswordChangeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True, write_only=True)
    new_password1 = PasswordField(max_length=64)
    new_password2 = PasswordField()

    class Meta:
        model = User
        fields = ['password', 'new_password1', 'new_password2']

    def validate_password(self, password):
        if not self.instance.check_password(password):
            raise serializers.ValidationError(_('Incorrect password.'))
        return password

    def validate(self, data):
        if len(data['new_password1']) < pass_min_length:
            raise serializers.ValidationError(
                {"new_password": _(f"Password must contain at least {pass_min_length} characters.")})
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password": _("The two password fields didn't match.")})
        if data['new_password1'].isdigit():
            raise serializers.ValidationError({"new_password": _("This password is entirely numeric.")})
        if data['new_password1'] == data['password']:
            raise serializers.ValidationError({"new_password": _("New password is too similar to old.")})
        return data

    def update(self, instance, validated_data):
        new_password = validated_data.get("new_password1")
        instance.set_password(new_password)
        instance.save()
        return instance


class UserPasswordReset(serializers.ModelSerializer):
    password1 = PasswordField(max_length=64, required=True)
    password2 = PasswordField(max_length=64, required=True)

    class Meta:
        model = User
        fields = ['password1', 'password2']

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password1": _("The two password fields didn't match.")})
        if len(data['password1']) < pass_min_length:
            raise serializers.ValidationError({"password1": _(f"Password must contain at least {pass_min_length} characters.")})
        return data


class UserSerializer(DynamicFieldsModelSerializer):
    username = serializers.CharField(min_length=4, max_length=30, required=False, validators=[UsernameValidator])
    email = serializers.EmailField(min_length=4, max_length=60, required=False)
    slug = serializers.CharField(read_only=True)
    first_name = serializers.CharField(max_length=30, required=False, validators=[UsernameValidator])
    last_name = serializers.CharField(max_length=30, required=False, validators=[UsernameValidator])
    phone_number = serializers.CharField(min_length=9, max_length=20, required=False, validators=[PhoneNumberValidator])
    short_bio = serializers.CharField(max_length=60, required=False)
    about_me = serializers.CharField(max_length=500, required=False)
    birth_date = serializers.DateField(format="%d-%m-%Y", input_formats=['%d-%m-%Y', 'iso-8601'], required=False)
    address = serializers.CharField(max_length=200, required=False)
    gender = serializers.ChoiceField(choices=Gender.choices, default=Gender.NONE, required=False)
    picture = serializers.ImageField(required=False)
    geolocation = serializers.CharField(required=False, validators=[GeoLocationValidator])
    is_private = serializers.BooleanField(default=False)
    receive_sms = serializers.BooleanField(default=False)
    is_verified = serializers.BooleanField(read_only=True)
    is_official = serializers.BooleanField(read_only=True)
    has_brand = serializers.BooleanField(read_only=True)
    followings_brand = BrandSerializer(many=True, read_only=True, fields=['name', 'logo', 'slogan', 'suffix'])
    city = CitySerializer(required=False)

    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'uuid': {'read_only': True},
            'slug': {'read_only': True},
        }
        depth = 1

    def to_representation(self, instance):
        data = super().to_representation(instance)
        count_strokes = ['followings_count_brand', 'followings_count_user', 'followers_count', 'account_views']
        input_fields = self.context.get('fields')
        for stroke in count_strokes:
            if input_fields is not None and stroke in input_fields:
                count = r.get(f"user:{instance.pk}:{stroke}")
                if stroke == 'account_views':
                    count = len(r.zrange(f"user:views:{instance.pk}", 0, -1))
                data[stroke] = int(count) if count else 0
        try:
            brand = instance.brand_user.brand
            has_brand = True
            data['is_manager'] = instance.brand_user.is_manager
            data['brand'] = instance.brand_user.brand.name
        except:
            has_brand = False
        data['has_brand'] = has_brand
        return data

    def validate_username(self, username):
        if User.objects.filter(Q(username__iexact=username)) \
                .exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError(_('User with that username is already exists.'))
        if '@' in username or '+' in username:
            raise serializers.ValidationError(_('Symbols "@" or "+" are not allowed in username.'))
        return username

    def validate_email(self, email):
        if User.objects.filter(Q(email__iexact=email)) \
                .exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError(_('User with that email already exists.'))
        return email

    @staticmethod
    def validate_birth_date(date):
        if int(date.year) < MINIMUM_BIRTH_YEAR:
            raise serializers.ValidationError(_(f"Minimum birth year is {MINIMUM_BIRTH_YEAR}'s year!"))
        if int(date.year) > MAXIMUM_BIRTH_YEAR:
            raise serializers.ValidationError(_(f"Maximum birth year is {MAXIMUM_BIRTH_YEAR}'s year!"))
        return date

    @staticmethod
    def validate_phone_number(phone_number):
        strict_number = phone_number.replace(' ', '')[-9:]
        if User.objects.filter(Q(phone_number=strict_number)).exists():
            raise serializers.ValidationError(_('User with that phone number already exists.'))
        return strict_number

    @staticmethod
    def validate_geolocation(location):
        try:
            lat = location.split()[0].replace(',', '')
            lon = location.split()[1]
        except Exception:
            raise serializers.ValidationError(_("Wrong location input. Example: '42.123456, 60.654321'"))
        location = f'{lat}, {lon}'
        return location

    def update(self, instance, validated_data):
        city = validated_data.pop('city', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if city is not None:
            instance.city = city_get(city)
        instance.save()
        return instance
