import secrets
import uuid

from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.db import models

from other.fields import OrderField
from other.validators import UsernameValidator, NameValidator, TitleValidator, PhoneNumberValidator


def get_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    brand = instance.suffix.lower()
    file_name = f'{brand}-{secrets.token_hex(2)}.{ext}'
    return f'brands/{brand}/{file_name}'


class Brand(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    """Brand"""
    owner = models.OneToOneField(get_user_model(),
                                 on_delete=models.SET_NULL,
                                 related_name='brand', null=True)
    name = models.CharField(_('name'), max_length=60, unique=True, db_index=True, validators=[TitleValidator])
    email = models.EmailField(_('email'), max_length=60, unique=True, blank=True, null=True)
    phone_number = models.CharField(_('phone number'), max_length=20, unique=True)
    suffix = models.CharField(_('suffix'), max_length=50, unique=True, validators=[UsernameValidator])
    slug = models.CharField(_('slug'), max_length=50, unique=True, blank=True)
    info = models.TextField(_('info'), max_length=500, blank=True, null=True)
    slogan = models.CharField(_('slogan'), max_length=60, blank=True, null=True)
    rating = models.PositiveIntegerField(_('rating'), default=0, blank=True)
    delivery = models.BooleanField(_('delivery'), default=False)
    """File upload"""
    logo = models.ImageField(_('logo'), upload_to=get_upload_path, blank=True, null=True)
    poster = models.FileField(_('poster'), upload_to=get_upload_path, blank=True, null=True)
    advert = models.FileField(_('advertisement'), upload_to=get_upload_path, blank=True, null=True)
    """Parameters"""
    is_active = models.BooleanField(_('active'), default=True)
    status = models.BooleanField(_('status'), default=True)
    verified = models.BooleanField(_('verified'), default=False)
    """Location"""
    address = models.CharField(_('address'), max_length=200, blank=True, null=True)
    cities = models.ManyToManyField("other.City", blank=True)
    geolocation = models.CharField(_('geolocation'), max_length=100, blank=True, null=True)
    """Info"""
    created_at = models.DateTimeField(_('created date'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated date'), auto_now=True)
    """Follow"""
    followers = models.ManyToManyField(get_user_model(),
                                       through='Contact',
                                       symmetrical=False,
                                       related_name='followings_brand')

    def save(self, *args, **kwargs):
        self.suffix = self.suffix.lower()
        self.slug = slugify(self.suffix, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Brand, self).__init__(*args, **kwargs)

    class Meta:
        ordering = ('-pk',)


class BrandUser(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE,
                              related_name='brand_user')
    user = models.OneToOneField(get_user_model(),
                                on_delete=models.CASCADE,
                                related_name='brand_user')
    is_manager = models.BooleanField(_('manager'), default=False)
    created_at = models.DateTimeField(_('created date'), auto_now_add=True)

    def __str__(self):
        if self.is_manager:
            status = 'manager'
        else:
            status = 'seller'
        return f"'{self.user}' - '{status}' for '{self.brand}'"


class BrandCustomerContacts(models.Model):
    contact = models.CharField(max_length=50, validators=[PhoneNumberValidator])
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='contacts')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return f'{self.brand} - contact - {self.contact}'


class Contact(models.Model):
    from_user = models.ForeignKey(get_user_model(),
                                  related_name='rel_from',
                                  on_delete=models.CASCADE)
    to_brand = models.ForeignKey(Brand,
                                 blank=True, null=True,
                                 related_name='rel_to_brand',
                                 on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.from_user} following {self.to_brand}'


class OwnCategory(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=20, validators=[NameValidator])
    slug = models.SlugField(max_length=25, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='own_category')
    description = models.CharField(max_length=300, blank=True, null=True)
    order = OrderField(blank=True, for_fields=['brand'], start=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('order',)
        verbose_name = 'Own Category'
        verbose_name_plural = 'Own Categories'

    def __str__(self):
        return f"'{self.brand}' category: '{self.name}'"

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BrandUserRequest(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE,
                              related_name='brand_user_request')
    user = models.ForeignKey(get_user_model(),
                             on_delete=models.CASCADE,
                             related_name='brand_user_request')
    is_manager = models.BooleanField(_('manager'), default=False)
    comment = models.CharField(_('comment'), max_length=200, blank=True, null=True)
    status = models.BooleanField(_('status'), default=True)
    created_at = models.DateTimeField(_('created date'), auto_now_add=True)
