from django.db.models.signals import post_save, post_delete
from django_redis import get_redis_connection

from .models import Follow

r = get_redis_connection("default")


def followers_changed(instance, *args, **kwargs):
    if instance.status:
        from_user, to_user = instance.from_user, instance.to_user
        followings_count_user = Follow.objects.filter(from_user=from_user, status=True).count()
        followers_count = Follow.objects.filter(to_user=to_user, status=True).count()
        r.set(f"user:{from_user.pk}:followings_count_user", followings_count_user)
        r.set(f"user:{to_user.pk}:followers_count", followers_count)


post_save.connect(followers_changed, sender=Follow)
post_delete.connect(followers_changed, sender=Follow)
