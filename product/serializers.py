from rest_framework import serializers
from django_redis import get_redis_connection
from django.utils.translation import ugettext_lazy as _

from actions.utils import brand_create_action
from brand.serializers import BrandSerializer, OwnCategorySerializer
from other.utils import tag_get_or_create, size_get_or_create, color_get, category_get, type_get_all_or_create, \
    type_get, own_category_get_other_or_create, own_category_get
from other.serializers import SubCategorySerializer, TagSerializer, ColorSerializer, SizeSerializer, TypeSerializer
from other.validators import NameValidator, TitleValidator
from other.choices import Verb
from .models import Product, ProductImage

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


class ProductImageSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'
        extra_kwargs = {
            "order": {'read_only': True},
            "product": {'read_only': True},
            "is_main": {'read_only': True},
            "image": {'required': True}
        }

    def to_internal_value(self, data):
        image = data
        return image


class ProductCreateSerializer(DynamicFieldsModelSerializer):
    brand = BrandSerializer(fields=['name', 'suffix', 'logo', 'rating', 'slug'], read_only=True)
    images = ProductImageSerializer(many=True, fields=['image', 'order', 'is_main'], required=False)
    category = SubCategorySerializer(fields=['name', 'slug', 'type'], required=False)
    type = TypeSerializer(fields=['type', 'slug'], required=False)
    name = serializers.CharField(min_length=3, max_length=200, required=True, validators=[TitleValidator])
    own_category = OwnCategorySerializer(fields=['name', 'slug'], required=False)
    tags = TagSerializer(many=True, fields=['name', 'slug'], required=False)
    color = ColorSerializer(many=True, required=False)
    vendor_code = serializers.CharField(min_length=1, max_length=40, required=False)
    origin = serializers.CharField(min_length=1, max_length=50, required=False)
    sizes = SizeSerializer(many=True, fields=['size'], required=False)
    description = serializers.CharField(max_length=10000, required=False)
    barcode = serializers.IntegerField(required=False)
    price = serializers.IntegerField(min_value=1, max_value=100000000, required=True)
    old_price = serializers.IntegerField(min_value=1, max_value=100000000, required=False)
    stock = serializers.IntegerField(min_value=0, max_value=100000000, default=1, required=False)
    discount = serializers.IntegerField(min_value=1, max_value=100, required=False)
    status = serializers.BooleanField(default=True, required=False)
    is_sale = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = Product
        fields = '__all__'
        extra_kwargs = {
            "user": {'read_only': True},
            "slug": {'read_only': True},
            "is_active": {'read_only': True},
        }
        depth = 1

    def create(self, validated_data):
        tags = validated_data.pop('tags', None)
        sizes = validated_data.pop('sizes', None)
        type_ = validated_data.pop('type', None)
        color = validated_data.pop('color', None)
        category = validated_data.pop('category', None)
        own_category = validated_data.pop('own_category', None)
        product = Product.objects.create(**validated_data)
        if type_ == 'all' or type_ is None:
            product.type = type_get_all_or_create()
        else:
            product.type = type_get(type_)
        if own_category == 'other' or own_category is None or own_category == '' or own_category == ' ':
            product.own_category = own_category_get_other_or_create(validated_data['brand'])
        else:
            product.own_category = own_category_get(own_category, validated_data['brand'])
        if tags is not None:
            product.tags.set(tag_get_or_create(tags, product.user.user))
        if sizes is not None:
            product.sizes.set(size_get_or_create(sizes))
        if color is not None:
            product.color.set(color_get(color))
        product.category = category_get(category, type_)
        product.save()
        brand_create_action(product.brand, Verb.PRODUCT, product)
        return product


class ProductSerializer(DynamicFieldsModelSerializer):
    brand = BrandSerializer(fields=['name', 'suffix', 'logo', 'rating', 'slug', 'geolocation', 'contacts'], read_only=True)
    images = ProductImageSerializer(many=True, fields=['image', 'order', 'is_main'], read_only=True)
    name = serializers.CharField(min_length=3, max_length=200, required=False, validators=[TitleValidator])
    type = TypeSerializer(fields=['type', 'slug'], required=False)
    category = SubCategorySerializer(fields=['name', 'slug', 'type'], read_only=True)
    own_category = OwnCategorySerializer(fields=['name', 'slug'], required=False)
    tags = TagSerializer(many=True, required=False)
    color = ColorSerializer(many=True, required=False)
    vendor_code = serializers.CharField(min_length=1, max_length=40, required=False)
    origin = serializers.CharField(min_length=1, max_length=50, required=False)
    sizes = SizeSerializer(many=True, fields=['size'], required=False)
    description = serializers.CharField(max_length=10000, required=False)
    barcode = serializers.IntegerField(required=False)
    price = serializers.IntegerField(min_value=1, max_value=100000000, required=False)
    old_price = serializers.IntegerField(min_value=1, max_value=100000000, required=False)
    stock = serializers.IntegerField(min_value=0, max_value=100000000, default=1, required=False)
    discount = serializers.IntegerField(min_value=1, max_value=100, required=False)
    status = serializers.BooleanField(default=True, required=False)
    is_sale = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = Product
        fields = '__all__'
        extra_kwargs = {
            "user": {'read_only': True},
            "slug": {'read_only': True},
            "is_active": {'read_only': True},
            "created_at": {'format': '%Y-%m-%d'}
        }
        depth = 1

    def to_representation(self, instance):
        counting_strokes = ['product_views', 'like_count', 'rating_count']
        data = super().to_representation(instance)
        input_fields = self.context.get('fields')
        for stroke in counting_strokes:
            if input_fields is not None and stroke in input_fields:
                count = r.get(f"product:{instance.pk}:{stroke}")
                if stroke == 'product_views':
                    count = len(r.zrange(f"product:views:{instance.pk}", 0, -1))
                data[stroke] = int(count) if count else 0
        return data

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        sizes = validated_data.pop('sizes', None)
        type_ = validated_data.pop('type', None)
        color = validated_data.pop('color', None)
        category = validated_data.pop('category', None)
        own_category = validated_data.pop('own_category', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if type_ == 'all' or type_ is None:
            instance.type = type_get_all_or_create()
        else:
            instance.type = type_get(type_)
        if own_category == 'other' or own_category is None or own_category == '' or own_category == ' ':
            instance.own_category = own_category_get_other_or_create(instance.brand)
        else:
            instance.own_category = own_category_get(own_category, instance.brand)
        if tags is not None:
            instance.tags.set(tag_get_or_create(tags, instance.user.user))
        if sizes is not None:
            instance.sizes.set(size_get_or_create(sizes))
        if color is not None:
            instance.color.set(color_get(color))
        if category is not None:
            instance.category = category_get(category, type_)
        instance.save()
        return instance
