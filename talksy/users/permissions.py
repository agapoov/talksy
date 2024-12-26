from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class UserNotBlocked(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True
        if request.user.is_blocked:
            raise PermissionDenied(detail="User blocked")

        return True
