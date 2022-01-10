from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from django_redis import get_redis_connection

from brand.models import Brand, BrandUser, OwnCategory, BrandCustomerContacts
from other.validators import PhoneNumberValidator, GeoLocationValidator, UsernameValidator, NameValidator, \
    TitleValidator
from other.serializers import CitySerializer

from accounts.export_serializers import UserSerializer

r = get_redis_connection("default")


class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class BrandContactSerializer(DynamicFieldsModelSerializer):
    contact = serializers.CharField(min_length=9, max_length=20, validators=[PhoneNumberValidator], required=False)

    class Meta:
        model = BrandCustomerContacts
        fields = ["contact", "brand"]

    @staticmethod
    def validate_contact(contact):
        strict_number = contact.replace(' ', '')[-9:]
        if not strict_number.isdigit() or len(strict_number) < 9:
            raise serializers.ValidationError(_('Input valid phone number'))
        return strict_number

    def to_representation(self, instance):
        return instance.contact

    def create(self, validated_data):
        BrandCustomerContacts.objects.create(**validated_data)

class BrandRegisterSerializer(DynamicFieldsModelSerializer):
    name = serializers.CharField(min_length=3, max_length=60, required=True, validators=[TitleValidator])
    email = serializers.EmailField(min_length=6, max_length=60, required=True)
    phone_number = serializers.CharField(max_length=20, validators=[PhoneNumberValidator], required=True)
    """Not required"""
    cities = CitySerializer(many=True, required=False)
    suffix = serializers.CharField(min_length=2, max_length=50, required=False, validators=[UsernameValidator])
    info = serializers.CharField(max_length=500, required=False)
    slogan = serializers.CharField(max_length=60, required=False)
    address = serializers.CharField(max_length=200, required=False)
    geolocation = serializers.CharField(required=False, validators=[GeoLocationValidator])
    logo = serializers.ImageField(required=False)
    poster = serializers.FileField(required=False)
    status = serializers.BooleanField(default=True, required=False)

    class Meta:
        model = Brand
        fields = '__all__'

    @staticmethod
    def validate_name(name):
        if Brand.objects.filter(Q(name__iexact=name)).exists():
            raise serializers.ValidationError(_('Brand with that name already registered.'))
        return name

    @staticmethod
    def validate_suffix(suffix):
        if Brand.objects.filter(Q(suffix__iexact=suffix)).exists():
            raise serializers.ValidationError(_('Brand with that suffix already registered.'))
        return suffix

    @staticmethod
    def validate_email(email):
        if Brand.objects.filter(Q(email__iexact=email)).exists():
            raise serializers.ValidationError(_('Brand with that email already registered.'))
        return email

    @staticmethod
    def validate_phone_number(phone_number):
        strict_number = phone_number.replace(' ', '').replace('-', '')[-9:]
        if not strict_number.isdigit() or len(strict_number) < 9:
            raise serializers.ValidationError(_('Input valid phone number or email'))
        if Brand.objects.filter(Q(phone_number=strict_number)).exists():
            raise serializers.ValidationError(_('Brand with that phone number already registered.'))
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

    def create(self, validated_data):
        cities = validated_data.pop('cities', None)
        if not validated_data.get('suffix'):
            validated_data['suffix'] = validated_data.get('name').strip().replace(" ", "-")[0:10]
            while Brand.objects.filter(Q(suffix__iexact=validated_data['suffix'])).exists():
                validated_data['suffix'] = f'{str(validated_data["suffix"])}-'
        brand = Brand.objects.create(**validated_data)
        if cities is not None:
            brand.cities.set(cities)
        BrandUser.objects.create(brand=brand, user=brand.owner, is_manager=True)
        return brand


class BrandSerializer(DynamicFieldsModelSerializer):
    name = serializers.CharField(min_length=3, max_length=60, required=False, validators=[TitleValidator])
    email = serializers.EmailField(min_length=6, max_length=60, required=False)
    phone_number = serializers.CharField(min_length=9, max_length=20, validators=[PhoneNumberValidator], required=False)
    suffix = serializers.CharField(min_length=2, max_length=50, required=False, validators=[UsernameValidator])
    contacts = BrandContactSerializer(many=True, required=False)
    cities = CitySerializer(many=True, required=False)
    info = serializers.CharField(max_length=500, required=False)
    slogan = serializers.CharField(max_length=60, required=False)
    address = serializers.CharField(max_length=200, required=False)
    geolocation = serializers.CharField(required=False, validators=[GeoLocationValidator])
    logo = serializers.ImageField(required=False)
    poster = serializers.FileField(required=False)
    delivery = serializers.BooleanField(default=False, required=False)
    status = serializers.BooleanField(default=True, required=False)
    """Relations"""
    owner = UserSerializer(read_only=True, fields=['username', 'picture', 'first_name', 'last_name', 'slug'])
    followers = UserSerializer(read_only=True, many=True,
                               fields=['username', 'picture', 'first_name', 'last_name', 'slug'])

    class Meta:
        model = Brand
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'uuid': {'read_only': True},
            'is_active': {'read_only': True},
            'rating': {'read_only': True},
            'followers': {'read_only': True},
            'created_at': {'read_only': True, 'format': '%Y-%m-%d'},
            'updated_at': {'read_only': True, 'format': '%Y-%m-%d'},
        }

    def to_representation(self, instance):
        instance_data = super().to_representation(instance)
        context = self.context.get('fields')
        if context and 'followers_count' in context:
            data = r.get(f"brand:{instance.pk}:followers_count")
            instance_data['followers_count'] = int(data) if data else 0
        return instance_data

    def validate_name(self, name):
        if Brand.objects.filter(Q(name__iexact=name)) \
                .exclude(name=self.instance.name).exists():
            raise serializers.ValidationError({'detail': _('Brand with that name already exists.')})
        return name

    def validate_suffix(self, suffix):
        if Brand.objects.filter(Q(suffix__iexact=suffix)) \
                .exclude(suffix=self.instance.suffix).exists():
            raise serializers.ValidationError({'detail': _('Brand with that suffix already exists.')})
        return suffix

    def validate_email(self, email):
        if Brand.objects.filter(Q(email__iexact=email)) \
                .exclude(email=self.instance.email).exists():
            raise serializers.ValidationError({'detail': _('Brand with that email already exists.')})
        return email

    def validate_phone_number(self, phone_number):
        strict_number = phone_number.replace(' ', '')[-9:]
        if Brand.objects.filter(Q(phone_number=strict_number)) \
                .exclude(phone_number=self.instance.phone_number).exists():
            raise serializers.ValidationError({'detail': _('Brand with that phone number already exists.')})
        if not strict_number.isdigit() or len(strict_number) < 9:
            raise serializers.ValidationError(_('Input valid phone number'))
        return strict_number

    @staticmethod
    def validate_geolocation(location):
        try:
            lat = location.split(',')[0]
            lon = location.split(',')[1]
        except Exception:
            raise serializers.ValidationError({'detail': _("Wrong location input. Example: '42.123456,60.654321'")})
        location = f'{lat},{lon}'
        return location

    def update(self, instance, validated_data):
        cities = validated_data.pop('cities', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if cities is not None:
            instance.cities.set(cities)
        instance.save()
        return instance


class BrandUserSerializer(DynamicFieldsModelSerializer):
    brand = BrandSerializer(fields=['name', 'rating', 'logo', 'slogan', 'slug'], read_only=True)
    user = UserSerializer(fields=['username', 'slug', 'picture', 'first_name', 'last_name'], read_only=True)
    is_manager = serializers.BooleanField(required=False)

    class Meta:
        model = BrandUser
        fields = ['brand', 'user', 'is_manager']

    def update(self, instance, validated_data):
        instance.is_manager = validated_data.get('is_manager', instance.is_manager)
        instance.save()
        return instance


class BrandUserCreateSerializer(DynamicFieldsModelSerializer):
    user = serializers.CharField(min_length=4, max_length=30, required=True)
    is_manager = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = BrandUser
        fields = ['user', 'is_manager']

    def create(self, validated_data):
        brand_user = BrandUser.objects.create(**validated_data)
        return brand_user


class OwnCategoryCreateSerializer(DynamicFieldsModelSerializer):
    name = serializers.CharField(min_length=1, max_length=20, required=True, validators=[TitleValidator])
    brand = BrandSerializer(fields=['name', 'logo', 'slogan', 'suffix', 'slug', 'rating'],
                            read_only=True)
    description = serializers.CharField(max_length=300, required=False)

    class Meta:
        model = OwnCategory
        fields = '__all__'
        extra_kwargs = {
            'order': {'read_only': True},
            'uuid': {'read_only': True}
        }

    def create(self, validated_data):
        category = OwnCategory.objects.create(**validated_data)
        return category


class OwnCategorySerializer(DynamicFieldsModelSerializer):
    name = serializers.CharField(min_length=1, max_length=20, required=False, validators=[TitleValidator])
    brand = BrandSerializer(fields=['name', 'logo', 'slogan', 'suffix', 'slug', 'rating'],
                            read_only=True)
    description = serializers.CharField(max_length=300, required=False)
    order = serializers.IntegerField(required=False)

    class Meta:
        model = OwnCategory
        fields = '__all__'
        extra_kwargs = {
            'uuid': {'read_only': True},
            'slug': {'read_only': True}
        }

    def to_internal_value(self, data):
        if isinstance(data, str):
            own_category = get_object_or_404(OwnCategory, slug=data.lower())
        else:
            raise serializers.ValidationError()
        return own_category

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
