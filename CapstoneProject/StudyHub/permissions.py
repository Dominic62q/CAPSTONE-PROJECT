from rest_framework import permissions

class IsGroupOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow group owners to edit or delete the StudyGroup.
    Read permissions (GET, HEAD, OPTIONS) are allowed for all authenticated users.
    """

    def has_permission(self, request, view):
        # Authenticated users can perform any action defined in the ViewSet (e.g., list, create).
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS (GET, HEAD, OPTIONS) are always allowed for reading data.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the StudyGroup.
        return obj.created_by == request.user