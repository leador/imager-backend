from django.db.models.signals import post_save, post_delete
from django_redis import get_redis_connection

from .models import Contact

r = get_redis_connection("default")


def followers_changed(instance, *args, **kwargs):
    from_user, to_brand = instance.from_user, instance.to_brand
    followings_count_brand = Contact.objects.filter(from_user=from_user).count()
    followers_count = Contact.objects.filter(to_brand=to_brand).count()
    r.set(f"user:{from_user.pk}:followings_count_brand", followings_count_brand)
    r.set(f"brand:{to_brand.pk}:followers_count", followers_count)


post_save.connect(followers_changed, sender=Contact)
post_delete.connect(followers_changed, sender=Contact)
