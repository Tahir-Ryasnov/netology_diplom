from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):

    def has_permission_obj(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
