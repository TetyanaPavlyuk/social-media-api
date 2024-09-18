from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from social_media.models import Profile, Post, Comment, Like, Message
from social_media.serializers import (
    ProfileSerializer,
    ProfileImageSerializer,
    PostSerializer,
    CommentSerializer,
    LikeSerializer,
    MessageSerializer,
)


class ProfileViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def get_queryset(self):
        if self.action == "list":
            return (self.queryset
            .select_related("user")
            .prefetch_related(
                "posts__comments",
                "posts__likes",
                "sent_messages",
                "following",
                "followers"
            ))
        return self.queryset

    def get_serializer_class(self):
        if self.action == "upload_image":
            return ProfileImageSerializer
        return ProfileSerializer

    @action(
        methods=["POST"],
        detail=True,
        # permission_classes=[IsAuthenticated],
        url_path="upload-image",
    )
    def upload_image(self, request, pk=None):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_queryset(self):
        if self.action == "list":
            return (self.queryset
                    .select_related("author__user")
                    .prefetch_related(
                "comments",
                "likes"
            ))
        return self.queryset

    @action(
        methods=["POST"],
        detail=True,
        url_path="like",
    )
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user
        owner = Profile.objects.get(user=user)

        like, created = Like.objects.get_or_create(owner=owner, post=post)

        if not created:
            like.delete()
            return Response({"detail": "Post unliked"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Post liked"}, status=status.HTTP_201_CREATED)


class CommentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_queryset(self):
        if self.action == "list":
            return (self.queryset
                    .select_related("author__user", "post")
                    )
        return self.queryset


class MessageViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.select_related()
        return self.queryset
