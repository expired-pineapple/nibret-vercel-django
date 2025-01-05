from rest_framework import permissions

class CustomerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.role in ['agent', 'admin']
        )