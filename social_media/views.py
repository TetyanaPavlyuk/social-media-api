from rest_framework import mixins, status
from rest_framework.decorators import action, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from social_media.models import Profile, Post, Comment, Like, Message
from social_media.permissions import OwnerOrReadOnlyProfile, OwnerOrReadOnly
from social_media.serializers import (
    ProfileSerializer,
    ProfileImageSerializer,
    PostSerializer,
    CommentSerializer,
    MessageSerializer, PostListSerializer, PostRetrieveSerializer,
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
    permission_classes = (OwnerOrReadOnlyProfile,)

    def get_queryset(self):
        """Retrieve the user's profiles with filter"""
        username = self.request.query_params.get("username")
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")

        if self.action == "list":
            queryset = (self.queryset
            .select_related("user")
            .prefetch_related(
                "posts__comments",
                "posts__likes",
                "sent_messages",
                "following",
                "followers"
            ))
        else:
            queryset = self.queryset

        if username:
            queryset = queryset.filter(nickname__icontains=username)
        if first_name:
            queryset = queryset.filter(user__first_name__icontains=first_name)
        if last_name:
            queryset = queryset.filter(user__last_name__icontains=last_name)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "upload_image":
            return ProfileImageSerializer
        return ProfileSerializer

    def perform_create(self, serializer):
        if Profile.objects.filter(user=self.request.user).exists():
            raise ValidationError("User already has profile")
        serializer.save(user=self.request.user)

    @action(
        methods=["POST"],
        detail=True,
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
    permission_classes(OwnerOrReadOnly, )

    def get_queryset(self):
        if self.action == "list":
            return (self.queryset
                    .select_related("author__user")
                    .prefetch_related(
                "comments",
                "likes"
            ))
        if self.action == "retrieve":
            return self.queryset.prefetch_related("likes__author")
        return self.queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        if self.action == "retrieve":
            return PostRetrieveSerializer
        return PostSerializer

    def perform_create(self, serializer):
        author = Profile.objects.get(user=self.request.user)
        serializer.save(author=author)

    @action(
        methods=["POST"],
        detail=True,
        url_path="like",
    )
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user
        author = Profile.objects.get(user=user)

        like, created = Like.objects.get_or_create(author=author, post=post)

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
    permission_classes(OwnerOrReadOnly, )

    def get_queryset(self):
        if self.action == "list":
            return (self.queryset
                    .select_related("author__user", "post")
                    )
        return self.queryset

    def perform_create(self, serializer):
        author = Profile.objects.get(user=self.request.user)
        serializer.save(author=author)


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
    permission_classes(OwnerOrReadOnly, )

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.select_related()
        return self.queryset

    def perform_create(self, serializer):
        author = Profile.objects.get(user=self.request.user)
        serializer.save(author=author)
