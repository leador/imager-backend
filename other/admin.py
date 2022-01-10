from django.contrib import admin

from other.models import City, Category, SubCategory, Tag, Comment, Color, Size, RegisterSecretCode, Type, Banner

admin.site.register(City)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Comment)
admin.site.register(Color)
admin.site.register(Size)
admin.site.register(Type)
admin.site.register(Banner)
admin.site.register(RegisterSecretCode)

@admin.register(SubCategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'slug', 'name', 'type', 'parent', 'created_at')
    list_display_links = ('order',)
    list_editable = ('type',)
    list_filter = ('type', 'parent', 'order', 'created_at')
    search_fields = ('name',)
    list_per_page = 100
    ordering = ('order',)