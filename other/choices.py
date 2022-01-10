from django.db import models
from django.utils.translation import ugettext_lazy as _

from other.models import City


class Verb(models.TextChoices):
    NONE = ''
    NEW = 'NEW', _('New')
    LIKE = 'LIKE', _('Like')
    SALE = 'SALE', _('Sale')
    PROMO = 'PROMO', _('Promo')
    PRODUCT = 'PRODUCT', _('Product')
    CONTEST = 'CONTEST', _('Contest')


class Gender(models.TextChoices):
    MAN = 'man', _('Man')
    WOMAN = 'woman', _('Woman')
    NONE = 'none', _('None')


class Color(models.TextChoices):
    BLACK = 'black', _('Black')
    WHITE = 'white', _('White')
    RED = 'red', _('Red')
    GREEN = 'green', _('Green')
    BLUE = 'blue', _('Blue')
    YELLOW = 'yellow', _('Yellow')
    ORANGE = 'orange', _('Orange')
    BROWN = 'brown', _('Brown')
    GRAY = 'grey', _('Grey')
    SILVER = 'silver', _('Silver')
    CYAN = 'cyan', _('Cyan')
    PURPLE = 'purple', _('Purple')
    PINK = 'pink', _('Pink')


def city_choices_list():
    try:
        cities = [city.slug for city in City.objects.all()]
    except Exception as e:
        cities = []
        print(e)
    return cities


class Cities(models.TextChoices):
    TAS = 'tashkent', _('Tashkent')
    SAM = 'samarkand', _('Samarkand')
    KOK = 'kokand', _('Kokand')
    NAM = 'namangan', _('Namangan')
    AND = 'andijan', _('Andijan')
    KAR = 'karakalpakstan', _('Karakalpakstan')
    BUK = 'bukhara', _('Bukhara')
    URG = 'urgench', _('Urgench')
    QAR = 'qarshi', _('Qarshi')
    TER = 'termez', _('Termez')
    NAV = 'navoiy', _('Navoiy')
    SIR = 'sirdarya', _('Sirdarya')
    JIZ = 'jizzakh', _('Jizzakh')
