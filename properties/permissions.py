from rest_framework import permissions

class PropertyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
       
        if request.method in permissions.SAFE_METHODS:
            return True
            
       
        return request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.role in ['agent', 'admin']
        )

class AdminReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_staff and request.method in permissions.SAFE_METHODS)