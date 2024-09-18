from rest_framework.permissions import BasePermission, SAFE_METHODS


class OwnerOrReadOnly(BasePermission):
    """The owner has full access to their profile.
    Authenticated users can only view the profiles of other users."""
    def has_object_permission(self, request, view, obj):
        return bool(
            (
                request.method in SAFE_METHODS
                and request.user
                and request.user.is_authenticated
            ) or (
                obj.author == request.user
            )
        )
