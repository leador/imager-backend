from django.urls import path

from . import views

urlpatterns = [
    path('register/<str:phone_number>', views.BrandRegisterAPI.as_view(), name='brand_register'),
    path('regvalidate', views.ValidateBrandRegisterAPI.as_view(), name='brand_validate_register'),
    path('regvalidate_resend/<str:phone_number>', views.ValidateResendBrandRegisterAPI.as_view(), name='brand_validate_resend_register'),
    path('mybrand', views.MyBrandAPI.as_view(), name='brand_mybrand'),
    path('list', views.BrandListAPI.as_view(), name='brand_list'),
    path('search', views.BrandSearchListAPI.as_view(), name='brand_search_list'),
    path('contact/<str:contact>', views.BrandContactDetailAPI.as_view(), name='brand_contact_remove'),
    path('detail/<str:brand_slug>', views.BrandDetailAPI.as_view(), name='brand_detail'),
    path('follow/<str:brand_slug>/<str:action>', views.UserFollowingAPI.as_view(), name='brand_follow'),
    path('member/list/<str:brand_slug>', views.BrandMembersListAPI.as_view(), name='brand_member_list'),
    path('member/detail/<str:brand_slug>/<str:member>', views.BrandMemberDetailAPI.as_view(), name='brand_member_detail'),
    path('member/set-owner/<str:brand_slug>/<str:member>', views.BrandSetOwnerAPI.as_view(), name='brand_set_owner'),
    path('own-category/list/<str:brand_slug>', views.OwnCategoryListAPI.as_view(), name='brand_category_list'),
    path('own-category/detail/<str:brand_slug>/<str:uuid>', views.OwnCategoryDetailAPI.as_view(), name='brand_category_detail'),
]
