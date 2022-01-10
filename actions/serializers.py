from abc import ABC

from rest_framework import serializers

from actions.models import Action
from brand.serializers import BrandSerializer
from product.serializers import ProductSerializer
from product.models import Product


class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class ActionRelatedSerializer(serializers.RelatedField, ABC):

    def to_representation(self, value):
        if isinstance(value, Product):
            serializer = ProductSerializer(value, fields=['name', 'price', 'sale', 'slug'])
            # TODO: data images must return one(first) image
            return serializer.data
        raise Exception('Unexpected type of tagged object')


class ActionSerializer(DynamicFieldsModelSerializer):
    brand = BrandSerializer(fields=['name', 'logo', 'slogan', 'status'], required=False)
    target = ActionRelatedSerializer(read_only=True)

    class Meta:
        model = Action
        fields = ['brand', 'target', 'verb', 'seen']
        extra_kwargs = {
            'seen': {'read_only': True},
        }
