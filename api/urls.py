from django.urls import path, include

urlpatterns = [
    path('user/', include('accounts.urls')),
    path('brand/', include('brand.urls')),
    path('product/', include('product.urls')),
    path('other/', include('other.urls')),
]
