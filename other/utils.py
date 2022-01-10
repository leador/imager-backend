from rest_framework.generics import get_object_or_404

from brand.models import OwnCategory
from other.models import Tag, Size, Color, SubCategory, City, Type
from other.validators import validate_name


def tag_clear_set_or_create(tags, user):
    tags_list = tags.split(',')
    tag_models = []
    for tag in tags_list:
        clean_tag = tag.replace('#', '').strip().lower()
        validate_name(clean_tag)
        if Tag.objects.filter(name=clean_tag).exists():
            tag_model = Tag.objects.filter(name=clean_tag).first()
            tag_models.append(tag_model)
        else:
            tag_model = Tag.objects.create(name=clean_tag, user=user)
            tag_models.append(tag_model)
    return tag_models


def tag_get_or_create(tags, user):
    tag_models = []
    for tag in tags:
        if Tag.objects.filter(name__iexact=tag).exists():
            tag_model = Tag.objects.filter(slug=tag).first()
            tag_models.append(tag_model)
        else:
            tag_model = Tag.objects.create(name=tag, user=user)
            tag_models.append(tag_model)
    return tag_models


def size_get_or_create(sizes):
    size_models = []
    for size in sizes:
        size_model, created_size_model = Size.objects.get_or_create(size=size)
        size_models.append(size_model) if size_model is not None else size_models.append(created_size_model)
    return size_models


def color_get(colors):
    color_models = []
    for color in colors:
        color_model = Color.objects.filter(name=color).first()
        color_models.append(color_model)
    return color_models


def city_get(city):
    city = get_object_or_404(City, slug=str(city).lower())
    return city


def city_none_get_or_create():
    city_g, city_c = City.objects.get_or_create(city='None')
    return city_g if city_g else city_c


def type_get_all_or_create():
    type_g, type_c = Type.objects.get_or_create(type='All')
    return type_g if type_g else type_c

def type_get(_type):
    type_ = get_object_or_404(Type, slug=_type[0])
    return type_

def own_category_get_other_or_create(brand):
    own_category_g, own_category_c = OwnCategory.objects.get_or_create(name='Other', brand=brand)
    return own_category_g if own_category_g else own_category_c

def own_category_get(own_category, brand):
    own_category = get_object_or_404(OwnCategory, slug=own_category[0], brand=brand)
    return own_category

def category_get(category, type_):
    category = get_object_or_404(SubCategory, type__slug=type_[0], slug=category[0])
    return category


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip