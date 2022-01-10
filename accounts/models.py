import uuid
import unicodedata
import secrets

from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from other.validators import UsernameValidator
from other.choices import Gender


class CustomUserManager(UserManager):

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError(_('The given username must be set'))

        email = self.normalize_email(email)
        username = self.normalize_username(username)
        slug = username.lower()
        user = self.model(username=username, email=email, slug=slug, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, is_staff=False,
                                 is_superuser=False, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, is_official=True,
                                 is_staff=True, is_superuser=True, **extra_fields)

    @classmethod
    def normalize_username(cls, username):
        return unicodedata.normalize('NFKC', username) if isinstance(username, str) else username


def get_avatar_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    username = instance.username.lower()
    file_name = f'{username}-{secrets.token_hex(2)}.{ext}'
    return f'users/{username}/{file_name}'


class User(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    """User"""
    username = models.CharField(
        _('username'),
        max_length=30,
        unique=True,
        help_text=_('Required. 30 characters or fewer. Letters, digits and ".", "-", "_" only.'),
        db_index=True,
        validators=[UsernameValidator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    phone_number = models.CharField(_('phone number'), max_length=20, unique=True, db_index=True, blank=True, null=True)
    email = models.EmailField(_('email address'), max_length=60, unique=True, db_index=True, blank=True, null=True)
    slug = models.SlugField(_('slug'), max_length=60, unique=True, blank=True)
    """Profile"""
    picture = models.ImageField(_('picture'), upload_to=get_avatar_upload_path, blank=True, null=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True, null=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True, null=True)
    about_me = models.CharField(_('about me'), max_length=500, blank=True, null=True)
    short_bio = models.CharField(_('short biography'), max_length=60, blank=True, null=True)
    birth_date = models.DateField(_('birth date'), blank=True, null=True)
    gender = models.CharField(_('gender'), max_length=10, choices=Gender.choices, default=Gender.NONE)
    type = models.CharField(_('type'), max_length=20, blank=True, null=True)
    """Parameters"""
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_verified = models.BooleanField(_('verified'), default=False)
    is_official = models.BooleanField(_('official'), default=False)
    is_private = models.BooleanField(_('private'), default=False)
    receive_sms = models.BooleanField(_('receive SMS'), default=False)
    """Location"""
    address = models.CharField(_('address'), max_length=200, blank=True, null=True)
    city = models.ForeignKey('other.City', on_delete=models.SET_NULL, blank=True, null=True)
    geolocation = models.CharField(_('geolocation'), max_length=24, blank=True, null=True)
    # lat, lon = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    """Info"""
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    updated_at = models.DateTimeField(_('updated'), auto_now=True)
    """Follow"""
    followers_count = models.PositiveIntegerField(_('followers count'), default=0, blank=True)
    followings_count_user = models.PositiveIntegerField(_('followings count user'), default=0, blank=True)
    followings_count_brand = models.PositiveIntegerField(_('followings count brand'), default=0, blank=True)
    followings_user = models.ManyToManyField("self",
                                             through='accounts.Follow',
                                             symmetrical=False,
                                             related_name='followers')
    """ followers """
    """ followings_brand """
    """ followers_count """
    """ followings_count_user """
    """ followings_count_brand """

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.username.lower())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Follow(models.Model):
    from_user = models.ForeignKey(User,
                                  related_name='rel_from_user',
                                  on_delete=models.CASCADE)
    to_user = models.ForeignKey(User,
                                blank=True, null=True,
                                related_name='rel_to_user',
                                on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    allowed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"'{self.from_user}' following '{self.to_user}'"
