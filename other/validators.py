import datetime
import re

from django.core import validators
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions

_year = datetime.date.today().year
MINIMUM_BIRTH_YEAR = int(_year) - 90
MAXIMUM_BIRTH_YEAR = int(_year) - 4
AVAILABLE_YEAR_CHOICES = list(reversed(range(int(_year) - 90, int(_year) - 4)))


def validate_email(email):
    clean_email = bool(re.match(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', email))
    if clean_email is False:
        raise exceptions.ValidationError(_('Type correct email address.'))


def validate_name(name):
    clean_name = bool(re.match(r'^[ЁёА-яA-Za-z0-9_\.\s-]+$', name))
    if clean_name is False:
        raise exceptions.ValidationError({'detail': _('This value may contain only letters, '
                                                      'numbers, space, and ".", "-", "_" characters.')})


class _ASCIINameValidator(validators.RegexValidator):
    regex = r'^[ЁёА-яA-Za-z0-9_\.\s-]+$'
    message = _('This value may contain only letters, '
                'numbers, space, and ".", "-", "_" characters.')
    flags = re.UNICODE


class _UnicodeTitleValidator(validators.RegexValidator):
    regex = r'^[ЁёА-яA-Za-z0-9_\.\s\-!\"#$%&\'()*+,.:;<=>?@\^_`{|}~-]+$'
    message = _('This value may contain only letters, '
                'numbers, space, and other characters.')
    flags = re.UNICODE


class _ASCIIUsernameValidator(validators.RegexValidator):
    regex = r'^[A-Za-z0-9_\.-]+$'
    message = _('This value may contain only Latin letters, '
                'numbers, and ".", "-", "_" characters.')
    flags = re.ASCII


class _PhoneNumberValidator(validators.RegexValidator):
    regex = r'^[+]?[0-9]{1,4}(\s?[-]?[0-9]{1,4})+$'
    message = _('Phone number is incorrect.')


class _GeoLocationValidator(validators.RegexValidator):
    regex = r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$'
    message = _("Wrong location input. Example: '42.123456,69.654321'.")


NameValidator = _ASCIINameValidator()
TitleValidator = _UnicodeTitleValidator()
UsernameValidator = _ASCIIUsernameValidator()
PhoneNumberValidator = _PhoneNumberValidator()
GeoLocationValidator = _GeoLocationValidator()
