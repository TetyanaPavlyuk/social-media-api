from rest_framework import serializers

from social_media.models import Profile, Post, Comment, Like, Message
from user.serializers import UserSerializer


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "user", "nickname"]

class ProfileSerializer(serializers.ModelSerializer):
    following = serializers.PrimaryKeyRelatedField(many=True, queryset=Profile.objects.all())
    followers = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ["id", "user", "nickname", "bio", "photo", "birth_date", "following", "followers"]

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


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "author", "content", "image", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "post", "author", "content", "created_at"]


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["id", "post", "comment", "owner"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "sender", "recipient", "content", "created_at"]
