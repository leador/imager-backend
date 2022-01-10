from django_filters import rest_framework as df_filters
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from other.models import Category, SubCategory, City, Color, Type, Banner
from other.serializers import CategorySerializer, SubCategorySerializer, CitySerializer, ColorSerializer, \
    TypeSerializer, BannerSerializer


class CharArrayFilter(df_filters.BaseInFilter, df_filters.CharFilter):
    pass


class MainCategoryListAPI(APIView):

    @staticmethod
    def get(request):
        fields = ['id', 'name', 'slug', 'children']
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True, fields=fields)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class SubCategoryListAPI(APIView):

    @staticmethod
    def get(request, main_category_slug):
        fields = ['id', 'name', 'parent', 'slug', 'type']
        categories = SubCategory.objects.filter(parent__slug=main_category_slug)
        serializer = SubCategorySerializer(categories, many=True, fields=fields)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class BannerListAPI(APIView):

    @staticmethod
    def get(request):
        banners = Banner.objects.all()
        serializer = BannerSerializer(banners, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class TypeListAPI(APIView):

    @staticmethod
    def get(request):
        fields = ['id', 'type', 'slug', 'categories']
        cities = Type.objects.all()
        serializer = TypeSerializer(cities, many=True, fields=fields)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class CitiesListAPI(APIView):

    @staticmethod
    def get(request):
        fields = ['id', 'city', 'slug']
        cities = City.objects.all()
        serializer = CitySerializer(cities, many=True, fields=fields)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class ColorsListAPI(APIView):

    @staticmethod
    def get(request):
        fields = ['name']
        cities = Color.objects.all()
        serializer = ColorSerializer(cities, many=True, fields=fields)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
