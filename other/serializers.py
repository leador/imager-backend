from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from accounts.export_serializers import UserSerializer
from brand.export_serializers import BrandExportSerializer
from .models import City, Category, SubCategory, Tag, Comment, Color, Size, Type, Banner
from .validators import NameValidator, validate_name, PhoneNumberValidator, TitleValidator


class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class CitySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = City
        fields = "__all__"

    def to_representation(self, instance):
        return instance.city

    def to_internal_value(self, data):
        if isinstance(data, str):
            city = get_object_or_404(City, slug=data.lower())
        else:
            raise serializers.ValidationError()
        return city


class TypeSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Type
        fields = "__all__"

    def to_internal_value(self, data):
        if isinstance(data, str):
            type_ = get_object_or_404(Type, slug=data.lower())
        else:
            raise serializers.ValidationError()
        return type_


class BannerSerializer(DynamicFieldsModelSerializer):
    brand = BrandExportSerializer(fields=['slug', 'name', 'suffix', 'logo'])

    class Meta:
        model = Banner
        fields = "__all__"


class SubCategorySerializer(DynamicFieldsModelSerializer):
    type = TypeSerializer(fields=['type', 'slug'])

    class Meta:
        model = SubCategory
        fields = "__all__"

    def to_internal_value(self, data):
        if isinstance(data, str):
            category = get_object_or_404(SubCategory, slug=data.lower())
        else:
            raise serializers.ValidationError()
        return category


class CategorySerializer(DynamicFieldsModelSerializer):
    children = SubCategorySerializer(many=True, fields=['name', 'slug', 'type'])

    class Meta:
        model = Category
        fields = "__all__"


class TagSerializer(DynamicFieldsModelSerializer):
    user = UserSerializer(fields=['username', 'slug', 'picture', 'first_name', 'last_name'])
    name = serializers.CharField(max_length=50, validators=[TitleValidator])

    class Meta:
        model = Tag
        fields = "__all__"

    def to_representation(self, instance):
        return instance.name


class CommentSerializer(DynamicFieldsModelSerializer):
    user = UserSerializer(read_only=True,
                          fields=['username', 'first_name', 'picture', 'last_name', 'is_official', 'followers_count'])

    class Meta:
        model = Comment
        fields = "__all__"
        extra_kwargs = {
            "uuid": {'read_only': True},
            "used_to": {'read_only': True},
            "parent": {'read_only': True},
            "is_active": {'read_only': True},
            "created_at": {'format': '%Y-%m-%d %H:%M:%S'},
            "updated_at": {'format': '%Y-%m-%d %H:%M:%S'},
        }
        # depth = 1


class ColorSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Color
        fields = "__all__"

    def to_representation(self, instance):
        return instance.name

    def to_internal_value(self, data):
        if isinstance(data, str):
            color = get_object_or_404(Color, name=data.lower())
        else:
            raise serializers.ValidationError()
        return color


class SizeSerializer(DynamicFieldsModelSerializer):
    size = serializers.CharField(max_length=20)

    class Meta:
        model = Size
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True}
        }

    def to_representation(self, instance):
        return instance.size

    def to_internal_value(self, data):
        return data