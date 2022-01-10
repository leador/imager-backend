from .models import User, Follow
from django.contrib import admin
from rest_framework_simplejwt.token_blacklist.admin import OutstandingTokenAdmin
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken


class CustomOutstandingTokenAdmin(OutstandingTokenAdmin):
    def has_delete_permission(self, *args, **kwargs):
        return True


admin.site.unregister(OutstandingToken)
admin.site.register(OutstandingToken, CustomOutstandingTokenAdmin)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('followers_count', 'followings_count_user', 'followings_count_brand',
                       'id', 'uuid', 'updated_at', 'followings_user')
    list_per_page = 100


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'from_user', 'to_user', 'status', 'created_at']
    list_per_page = 100
