from django.db.models import Count
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status
from rest_framework.decorators import action, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from social_media.models import Profile, Post, Comment, Like, Message, Tag
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
    ProfileRetrieveSerializer, TagSerializer, ProfileFollowSerializer, ProfileUnfollowSerializer,
)
from social_media.tasks import publish_scheduled_posts


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
        elif self.action == "retrieve":
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
    def upload_image(self, request, pk=None):
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
    def follow(self, request, pk=None):
        profile_to_follow = self.get_object()

        serializer = ProfileFollowSerializer(
            data={"profile_to_follow": profile_to_follow.id},
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

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
    def unfollow(self, request, pk=None):
        profile_to_unfollow = self.get_object()

        serializer = ProfileUnfollowSerializer(
            data={"profile_to_unfollow": profile_to_unfollow.id},
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": f"Successfully unfollowed {profile_to_unfollow.nickname}"},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="nickname",
                description="Filter by nickname",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="first_name",
                description="Filter by first name",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="last_name",
                description="Filter by last name",
                required=False,
                type=str
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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
                "comments", "likes", "tags"
            )
        elif self.action == "retrieve":
            queryset = self.queryset.prefetch_related("likes__author", "tags")
        else:
            queryset = self.queryset

        profile = self.request.user.profile
        following_profiles = profile.following.all()
        queryset = queryset.filter(
            author__in=[profile.id] + [profile.id for profile in following_profiles]
        )

        tag_name = self.request.query_params.get("tag")
        if tag_name:
            queryset = queryset.filter(tags__name__iexact=tag_name)

        queryset = queryset.filter(is_published=True)

        queryset = queryset.annotate(like_count=Count("likes")).annotate(comments_count=Count("comments"))

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        if self.action == "retrieve":
            return PostRetrieveSerializer
        return PostSerializer

    def perform_create(self, serializer):
        author = Profile.objects.get(user=self.request.user)
        post = serializer.save(author=author)
        if post.scheduled_at:
            publish_scheduled_posts.apply_async((post.id, ), eta=post.scheduled_at)
        else:
            post.is_published = True
            post.save()

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

    @action(methods=["GET"], detail=False, url_path="liked")
    def liked(self, request):
        profile = request.user.profile
        liked_posts = Post.objects.filter(likes__author=profile.id)
        serializer = PostListSerializer(liked_posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="tag",
                description="Filter by tag",
                required=False,
                type=str
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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


class TagViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes(IsAuthenticated, )
