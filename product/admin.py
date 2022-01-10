from django.contrib import admin

from .models import Product, ProductImage, ProductLike, ProductRating

admin.site.register(ProductImage)
admin.site.register(ProductLike)


@admin.register(ProductRating)
class ProductRatingAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    @staticmethod
    def get_user(obj):
        return obj.user.user.username

    readonly_fields = ('slug', 'created_at', 'updated_at')
    list_display = ('pk', 'name', 'brand', 'get_user', 'status', 'stock',
                    'slug', 'created_at',)
    list_display_links = ('name',)
    list_editable = ('status',)
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('brand', 'user', 'name')
    list_per_page = 100
