from gc import get_objects

from rest_framework import mixins, status
from rest_framework.decorators import action, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from social_media.models import Profile, Post, Comment, Like, Message
from social_media.permissions import OwnerOrReadOnlyProfile, OwnerOrReadOnly
from social_media.serializers import (
    ProfileSerializer,
    ProfileImageSerializer,
    PostSerializer,
    CommentSerializer,
    MessageSerializer,
    PostListSerializer,
    PostRetrieveSerializer,
    ProfileListSerializer,
    ProfileRetrieveSerializer,
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
        nickname = self.request.query_params.get("nickname")
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")

        if self.action == "list":
            queryset = self.queryset.select_related("user").prefetch_related(
                "posts__comments",
                "posts__likes",
                "sent_messages",
                "following",
                "followers",
            )
        if self.action == "retrieve":
            queryset = self.queryset.select_related()
        else:
            queryset = self.queryset

        if nickname:
            queryset = queryset.filter(nickname__icontains=nickname)
        if first_name:
            queryset = queryset.filter(user__first_name__icontains=first_name)
        if last_name:
            queryset = queryset.filter(user__last_name__icontains=last_name)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return ProfileListSerializer
        if self.action == "retrieve":
            return ProfileRetrieveSerializer
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
    def upload_image(self, request):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["POST"],
        detail=True,
        url_path="follow",
        permission_classes=(IsAuthenticated,),
    )
    def follow(self, request):
        profile_to_follow = self.get_object()
        user_profile = request.user.profile

        if profile_to_follow == user_profile:
            return Response(
                {"detail": "You can't follow yourself!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if profile_to_follow in user_profile.following.all():
            return Response(
                {"detail": "You already follow this user!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_profile.following.add(profile_to_follow)
        return Response(
            {"detail": f"Successfully followed {profile_to_follow.nickname}"},
            status=status.HTTP_200_OK,
        )

    @action(
        methods=["POST"],
        detail=True,
        url_path="unfollow",
        permission_classes=(IsAuthenticated,),
    )
    def unfollow(self, request):
        profile_to_unfollow = self.get_object()
        user_profile = request.user.profile

        if profile_to_unfollow == user_profile:
            return Response(
                {"detail": "You can't unfollow yourself!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if profile_to_unfollow not in user_profile.following.all():
            return Response(
                {"detail": "You are not following this user!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_profile.following.remove(profile_to_unfollow)
        return Response(
            {"detail": f"Successfully unfollowed {profile_to_unfollow.nickname}"},
            status=status.HTTP_200_OK,
        )


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
    permission_classes(
        OwnerOrReadOnly,
    )

    def get_queryset(self):
        if self.action == "list":
            queryset = self.queryset.select_related("author__user").prefetch_related(
                "comments", "likes"
            )
        if self.action == "retrieve":
            queryset = self.queryset.prefetch_related("likes__author")
        else:
            queryset = self.queryset

        profile = self.request.user.profile
        following_profiles = profile.following.all()
        queryset = queryset.filter(author__in=[profile.id] + [profile.id for profile in following_profiles])

        return queryset.order_by("-created_at")

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
            return Response(
                {"detail": "Post unliked"}, status=status.HTTP_204_NO_CONTENT
            )
        return Response({"detail": "Post liked"}, status=status.HTTP_201_CREATED)

    @action(
        methods=["GET"],
        detail=False,
        url_path="liked-posts"
    )
    def liked_posts(self, request):
        profile = request.user.profile
        liked_posts = Post.objects.filter(likes__author=profile.id)
        serializer = PostListSerializer(liked_posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
    permission_classes(
        OwnerOrReadOnly,
    )

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.select_related("author__user", "post")
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
    permission_classes(
        OwnerOrReadOnly,
    )

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.select_related()
        return self.queryset

    def perform_create(self, serializer):
        author = Profile.objects.get(user=self.request.user)
        serializer.save(author=author)
