from rest_framework import exceptions
from rest_framework.permissions import BasePermission


class IsAnonymous(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            raise exceptions.ParseError({'message': 'You are already logged in!'})
        return True
