from rest_framework.permissions import BasePermission, SAFE_METHODS


class OwnerOrReadOnlyProfile(BasePermission):
    """The owner has full access to their profile.
    Authenticated users can only view the profiles of other users."""

    def has_object_permission(self, request, view, obj):
        return bool(
            (
                request.method in SAFE_METHODS
                and request.user
                and request.user.is_authenticated
            )
            or (obj.user == request.user)
        )


class OwnerOrReadOnly(BasePermission):
    """The owner has full access to their posts, comments and likes.
    Authenticated users can only view the posts,
    comments and likes of other users."""

    def has_object_permission(self, request, view, obj):
        return bool(
            (
                request.method in SAFE_METHODS
                and request.user
                and request.user.is_authenticated
            )
            or (obj.author.user == request.user)
        )
