import secrets
import uuid

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from other.fields import OrderField
from other.validators import UsernameValidator, TitleValidator


class RegisterSecretCode(models.Model):
    secret_code = models.CharField(max_length=12)
    phone_or_email = models.CharField(max_length=50)
    title = models.CharField(max_length=60, validators=[TitleValidator], blank=True, null=True)
    username = models.CharField(max_length=30, validators=[UsernameValidator], blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    password = models.CharField(max_length=30, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('-pk',)

    def __str__(self):
        return f"{self.type} - {self.phone_or_email} - {self.secret_code}"


def get_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    brand = instance.brand.slug.lower()
    file_name = f'{brand}-{secrets.token_hex(2)}.{ext}'
    return f'banners/{brand}/{file_name}'


class Banner(models.Model):
    main = models.ImageField(_('main image'), upload_to=get_upload_path)
    mobile = models.ImageField(_('mobile image'), upload_to=get_upload_path)
    brand = models.ForeignKey("brand.Brand", on_delete=models.CASCADE, related_name='banner')
    slug = models.URLField(_('slug'), max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('pk',)

    def save(self, *args, **kwargs):
        self.slug = self.brand.slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand}-banner"


class Type(models.Model):
    type = models.CharField(max_length=50)
    slug = models.CharField(blank=True, max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('pk',)
        verbose_name = 'type'
        verbose_name_plural = 'types'

    def save(self, *args, **kwargs):
        self.type = self.type.title()
        self.slug = slugify(self.type.lower())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.type


class City(models.Model):
    city = models.CharField(max_length=50)
    slug = models.CharField(blank=True, max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('pk',)
        verbose_name = 'city'
        verbose_name_plural = 'cities'

    def save(self, *args, **kwargs):
        self.slug = slugify(self.city.lower(), allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.city


class Category(models.Model):
    name = models.CharField(max_length=50, validators=[TitleValidator])
    slug = models.CharField(max_length=55, blank=True)
    description = models.CharField(max_length=500, blank=True)
    order = OrderField(blank=True, start=1)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('order',)
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name.lower(), allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    name = models.CharField(max_length=50, validators=[TitleValidator])
    parent = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='children')
    type = models.ForeignKey(Type, on_delete=models.SET_NULL, null=True, related_name='categories')
    slug = models.CharField(max_length=55, blank=True)
    description = models.CharField(max_length=500, blank=True)
    # TODO redis used_count = models.PositiveIntegerField(default=0)
    order = OrderField(for_fields=['parent', 'type'], start=1, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('order',)
        verbose_name = _('sub category')
        verbose_name_plural = _('sub categories')

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name.lower(), allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, validators=[TitleValidator])
    slug = models.CharField(max_length=55, blank=True)
    user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)
    # TODO redis used_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('name',)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Comment(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name='my_comments')
    text = models.CharField(max_length=1000)
    used_to = models.ForeignKey("product.Product", on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True)
    is_active = models.BooleanField(default=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.user} commented to {self.used_to}"


class Color(models.Model):
    name = models.CharField(_('color'), max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('name',)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Size(models.Model):
    size = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('size',)

    def __str__(self):
        return self.size
