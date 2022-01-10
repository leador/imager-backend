from django.contrib import admin

from .models import Action


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('brand', 'verb', 'target', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('verb',)
