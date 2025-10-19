from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit objects"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsOwner(permissions.BasePermission):
    """Only owner can access"""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
