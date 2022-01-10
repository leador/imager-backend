import secrets

import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from other.fields import OrderField
from other.validators import NameValidator, TitleValidator


class Product(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    """Relations"""
    brand = models.ForeignKey("brand.Brand", on_delete=models.CASCADE)
    user = models.ForeignKey("brand.BrandUser", on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey("other.SubCategory", on_delete=models.SET_NULL, null=True)
    type = models.ForeignKey("other.Type", on_delete=models.SET_NULL, null=True)
    own_category = models.ForeignKey("brand.OwnCategory", on_delete=models.SET_NULL, blank=True, null=True)
    tags = models.ManyToManyField("other.Tag", blank=True)
    color = models.ManyToManyField("other.Color", blank=True)
    sizes = models.ManyToManyField("other.Size", blank=True)
    liked = models.ManyToManyField("accounts.User", through="ProductLike", blank=True, related_name='product_likes')
    rating = models.ManyToManyField("accounts.User", through="ProductRating", blank=True,
                                    related_name='product_ratings')
    """Product"""
    name = models.CharField(_("name"), max_length=200, db_index=True, validators=[TitleValidator])
    slug = models.SlugField(_("slug"), max_length=220, unique=True, blank=True)
    vendor_code = models.CharField(_("vendor code"), max_length=40, blank=True, null=True)
    origin = models.CharField(_("origin"), max_length=50, blank=True, null=True)
    barcode = models.CharField(_("barcode"), max_length=50, blank=True, null=True)
    discount = models.PositiveIntegerField(_("discount"), blank=True, null=True, validators=[
        MinValueValidator(1), MaxValueValidator(100)])
    price = models.DecimalField(_("price"), max_digits=19, decimal_places=0, default=0)
    old_price = models.DecimalField(_("old price"), max_digits=19, decimal_places=0, blank=True, null=True)
    stock = models.PositiveIntegerField(_("stock"), default=1)
    description = models.TextField(_("description"), max_length=10000, blank=True, null=True)
    """Parameters"""
    is_active = models.BooleanField(_("active"), default=True)
    status = models.BooleanField(_("status"), default=True)
    is_sale = models.BooleanField(_("sale"), default=False)
    """Info"""
    created_at = models.DateTimeField(_("created"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated"), auto_now=True)
    """product_views"""
    """like_count"""
    """rating_count"""

    def save(self, *args, **kwargs):
        if not self.slug:
            slug = slugify(self.name, allow_unicode=True)
            self.slug = f'{slug}-{secrets.token_hex(2)}'
        super().save(*args, **kwargs)

    def get_photo(self):
        photo = ProductImage.objects.filter(product=self, is_main=True).first()
        return photo.image

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-created_at',)


def get_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    brand = instance.product.brand.suffix
    file_name = f'{brand}-{secrets.token_hex(4)}.{ext}'
    product = instance.product.slug
    return f'brands/{brand}/products/{product}/{file_name}'


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=get_image_upload_path, max_length=200)
    order = OrderField(blank=True, for_fields=['product'], start=1)
    is_main = models.BooleanField(default=False, blank=True)

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return f'{self.product}-{self.order}'

    def save(self, *args, **kwargs):
        if self.order == 1:
            self.is_main = True
        super().save(*args, **kwargs)


class ProductRating(models.Model):
    user = models.ForeignKey("accounts.User",
                             related_name='rating_from_user',
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product,
                                related_name='rating_to_product',
                                on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=0, validators=[
        MaxValueValidator(5),
        MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)

    def __str__(self):
        return f'{self.user} rated {self.product} for {self.rating}'


class ProductLike(models.Model):
    user = models.ForeignKey("accounts.User",
                             related_name='like_from_user',
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product,
                                related_name='like_to_product',
                                on_delete=models.CASCADE)
    liked_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('-liked_at',)

    def __str__(self):
        return f'{self.user} liked {self.product}'
