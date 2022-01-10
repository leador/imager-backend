from django.urls import path

from . import views

urlpatterns = [
    path('list', views.ProductListAPI.as_view(), name='product_list'),
    path('following', views.FollowedBrandProductsAPI.as_view(), name='product_following'),
    path('search', views.ProductSearchListAPI.as_view(), name='product_search'),
    path('like/<str:product_slug>', views.ProductLikeAPI.as_view(), name='product_like'),
    path('comment/list/<str:product_slug>', views.ProductCommentAPI.as_view(), name='product_comment_list'),
    path('comment/detail/<str:uuid>', views.ProductCommentDetailAPI.as_view(), name='product_comment_detail'),
    path('rating/<str:product_slug>/<int:rating>', views.ProductRatingAPI.as_view(), name='product_rating'),
    path('detail/<str:product_slug>', views.ProductDetailAPI.as_view(), name='product_detail'),
    path('my/list', views.ProductMemberListAPI.as_view(), name='product_my_list'),
    path('my/detail/<str:product_slug>', views.ProductMemberDetailAPI.as_view(), name='product_mey_detail'),
]

