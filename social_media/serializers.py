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
        write_only=True
    )
    tags_display = TagSerializer(source="tags", many=True, read_only=True)

    class Meta:
        model = Post
        fields = ["id", "content", "image", "created_at", "tags", "tags_display"]

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)

        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            post.tags.add(tag)
        return post

    # def update(self, instance, validated_data):
    #     tags_data = validated_data.pop("tags", [])
    #     instance = super().update(instance, validated_data)
    #     instance.tags.set(tags_data)
    #     return instance


class PostListSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.nickname", read_only=True)
    tags = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    def get_tags(self, obj):
        return [element.name for element in obj.tags.all()]

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

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
        fields = ["id", "nickname", "bio", "photo", "birth_date"]


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


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["id", "post"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "recipient", "content", "created_at"]
