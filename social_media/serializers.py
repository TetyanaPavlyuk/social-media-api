from rest_framework import serializers

from social_media.models import Profile, Post, Comment, Like, Message, Tag


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "post", "content", "created_at"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class PostSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False,
    )
    tags_display = TagSerializer(source="tags", many=True, read_only=True)

    class Meta:
        model = Post
        fields = ["id", "content", "image", "created_at", "tags", "tags_display", "scheduled_at"]

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)

        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            post.tags.add(tag)
        return post

    def update(self, post, validated_data):
        tags_data = validated_data.pop("tags", [])
        post = super().update(post, validated_data)
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            post.tags.add(tag)
        return post


class PostListSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.nickname", read_only=True)
    tags = serializers.StringRelatedField(read_only=True, many=True, required=False)
    like_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "content",
            "image",
            "created_at",
            "tags",
            "like_count",
            "comments_count",
        ]


class PostRetrieveSerializer(PostSerializer):
    author = serializers.CharField(source="author.nickname", read_only=True)
    tags = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)

    def get_tags(self, obj):
        return [element.name for element in obj.tags.all()]

    def get_likes(self, obj):
        return [like.author.nickname for like in obj.likes.all()]

    class Meta:
        model = Post
        fields = ["id", "author", "content", "image", "created_at", "tags", "likes", "comments"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "user", "nickname", "bio", "birth_date"]
        read_only_fields = ["id", "user"]


class ProfileListSerializer(ProfileSerializer):
    following = serializers.SerializerMethodField()
    followers = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ["nickname", "bio", "photo", "following", "followers"]

    def get_following(self, obj):
        return obj.following.count()

    def get_followers(self, obj):
        return obj.followers.count()


class ProfileRetrieveSerializer(ProfileSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    following = serializers.SerializerMethodField()
    followers = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "nickname",
            "first_name",
            "last_name",
            "bio",
            "photo",
            "birth_date",
            "following",
            "followers",
        ]

    def get_following(self, obj):
        return [following.nickname for following in obj.following.all()]

    def get_followers(self, obj):
        return [followers.nickname for followers in obj.followers.all()]


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "photo"]


class ProfileFollowSerializer(serializers.ModelSerializer):
    profile_to_follow = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all()
    )

    class Meta:
        model = Profile
        fields = ["profile_to_follow"]

    def validate_profile_to_follow(self, profile_to_follow):
        user_profile = self.context["request"].user.profile

        if profile_to_follow == user_profile:
            raise serializers.ValidationError("You can't follow yourself!")

        if profile_to_follow in user_profile.following.all():
            raise serializers.ValidationError("You already follow this user!")

        return profile_to_follow

    def save(self, **kwargs):
        user_profile = self.context["request"].user.profile
        profile_to_follow = self.validated_data["profile_to_follow"]
        user_profile.following.add(profile_to_follow)
        return profile_to_follow


class ProfileUnfollowSerializer(serializers.ModelSerializer):
    profile_to_unfollow = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all()
    )

    class Meta:
        model = Profile
        fields = ["profile_to_unfollow"]

    def validate_profile_to_unfollow(self, profile_to_unfollow):
        user_profile = self.context["request"].user.profile

        if profile_to_unfollow == user_profile:
            raise serializers.ValidationError("You can't unfollow yourself!")

        if profile_to_unfollow not in user_profile.following.all():
            raise serializers.ValidationError("You are not following this user!")

        return profile_to_unfollow

    def save(self, **kwargs):
        user_profile = self.context["request"].user.profile
        profile_to_unfollow = self.validated_data["profile_to_unfollow"]
        user_profile.following.remove(profile_to_unfollow)
        return profile_to_unfollow


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["id", "post"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "recipient", "content", "created_at"]
