from django.contrib import admin

from .models import Brand, BrandUser, Contact, OwnCategory, BrandCustomerContacts


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    fields = ('name', 'owner', 'verified', 'status', 'is_active', 'delivery', 'email',
              'phone_number', 'suffix', 'slug', 'logo', 'poster', 'info', 'geolocation', 'address', 'cities',
              'rating', 'slogan', 'advert', 'created_at', 'updated_at', 'uuid', 'id')
    readonly_fields = ('created_at', 'updated_at', 'rating', 'uuid', 'id')
    list_display = ('name', 'owner', 'is_active', 'status', 'verified', 'email', 'phone_number', 'suffix',
                    'slug', 'created_at',)
    list_display_links = ('name', 'owner',)
    list_editable = ('status', 'verified', 'is_active')
    list_filter = ('created_at',)
    search_fields = ('owner', 'name', 'phone_number', 'suffix')
    list_per_page = 100


@admin.register(BrandUser)
class BrandUserAdmin(admin.ModelAdmin):

    @staticmethod
    def get_user(obj):
        return obj.user.username

    @staticmethod
    def owner(obj):
        try:
            return '+' if obj.user.brand else '-'
        except:
            return '-'

    fields = ('user', 'brand', 'is_manager', 'created_at', 'id')
    readonly_fields = ('created_at', 'id')
    list_display = ('get_user', 'brand', 'is_manager', 'owner', 'created_at',)
    list_display_links = ('get_user',)
    list_filter = ('created_at', 'is_manager', 'brand',)
    search_fields = ('get_user', 'brand')
    list_per_page = 100


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'from_user', 'to_brand', 'created_at']
    list_per_page = 100


@admin.register(OwnCategory)
class OwnCategoryUserAdmin(admin.ModelAdmin):
    fields = ('name', 'brand', 'description', 'order', 'id', 'uuid', 'created_at')
    readonly_fields = ('brand', 'id', 'uuid', 'created_at')
    list_display = ('__str__', 'order', 'name', 'brand')
    list_display_links = ('__str__',)
    list_filter = ('created_at', 'brand')
    search_fields = ('name', 'brand')
    list_per_page = 100

admin.site.register(BrandCustomerContacts)
