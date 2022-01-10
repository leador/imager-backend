from django.urls import path

from . import views

urlpatterns = [
    path('colors', views.ColorsListAPI.as_view(), name='other_colors_list'),
    path('types', views.TypeListAPI.as_view(), name='other_types_list'),
    path('cities', views.CitiesListAPI.as_view(), name='other_cities_list'),
    path('banners', views.BannerListAPI.as_view(), name='other_banners_list'),
    path('categories', views.MainCategoryListAPI.as_view(), name='other_categories_list'),
    path('subcategories/<str:main_category_slug>', views.SubCategoryListAPI.as_view(), name='other_subcategories_list'),
]