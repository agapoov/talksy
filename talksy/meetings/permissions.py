from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """"
    Custom permission allowing only the owner to edit
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.creator == request.user
