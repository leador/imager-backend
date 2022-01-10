from rest_framework import serializers
from accounts.models import User
from django_redis import get_redis_connection

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


class UserSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = User
        exclude = ['password']
        extra_kwargs = {
            'id': {'read_only': True},
            'uuid': {'read_only': True},
            'slug': {'read_only': True},
            'birth_date': {'format': '%Y-%m-%d'}
        }

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
        return data
