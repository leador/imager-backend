from django.db.models.signals import m2m_changed, post_save, post_delete
from django_redis import get_redis_connection

from .models import ProductLike, ProductRating, Product

r = get_redis_connection("default")


def image_is_main_checker(instance, *args, **kwargs):
    if instance.order == 1:
        instance.is_main = True
        instance.save()


def like_changed(instance, *args, **kwargs):
    user, product = instance.user, instance.product
    user_like_count = ProductLike.objects.filter(user=user).count()
    product_like_count = ProductLike.objects.filter(product=product).count()
    r.set(f"user:{user.pk}:like_count", user_like_count)
    r.set(f"product:{product.pk}:like_count", product_like_count)


def rating_changed(instance, *args, **kwargs):
    user, product = instance.user, instance.product
    user_rating_count = ProductRating.objects.filter(user=user).count()
    product_rating_count = ProductRating.objects.filter(product=product).count()
    r.set(f"user:{user.pk}:rating_count", user_rating_count)
    r.set(f"product:{product.pk}:rating_count", product_rating_count)


post_save.connect(like_changed, sender=ProductLike)
post_delete.connect(like_changed, sender=ProductLike)
post_save.connect(rating_changed, sender=ProductRating)
post_delete.connect(rating_changed, sender=ProductRating)
