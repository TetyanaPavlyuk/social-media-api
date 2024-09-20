from django.contrib.auth import get_user_model
from rest_framework import serializers

from social_media.models import Profile, Post, Comment, Like, Message


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "nickname"]

class ProfileSerializer(serializers.ModelSerializer):
    following = serializers.PrimaryKeyRelatedField(many=True, queryset=Profile.objects.all())
    followers = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ["id", "nickname", "bio", "photo", "birth_date", "following", "followers"]
        read_only_fields = ["id", "followers"]

    def update(self, instance, validated_data):
        following_data = validated_data.get("following", None)

        if following_data is not None:
            instance.following.add(*following_data)

        return super().update(instance, validated_data)

    def get_followers(self, obj):
        return FollowSerializer(obj.followers.all(), many=True).data


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "photo"]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "post", "content", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "content", "image", "created_at"]


class PostListSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.nickname", read_only=True)
    like_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    class Meta:
        model = Post
        fields = ["id", "author", "content", "image", "created_at", "like_count", "comments_count"]


class PostRetrieveSerializer(PostSerializer):
    author = serializers.CharField(source="author.nickname", read_only=True)
    likes = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)

    def get_likes(self, obj):
        return [like.author.nickname for like in obj.likes.all()]

    class Meta:
        model = Post
        fields = ["id", "author", "content", "image", "created_at", "likes", "comments"]


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["id", "post"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "recipient", "content", "created_at"]
