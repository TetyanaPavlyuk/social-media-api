import os
import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


def profile_image_path(instance: "Profile", filename: str) -> str:
    _, extention = os.path.splitext(filename)
    filename = f"{slugify(instance.nickname)}-{uuid.uuid4()}{extention}"
    return os.path.join("uploads/profile/", filename)


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    nickname = models.CharField(max_length=255, unique=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(null=True, blank=True, upload_to=profile_image_path)
    birth_date = models.DateField(null=True, blank=True)
    following = models.ManyToManyField(
        "self", related_name="followers", symmetrical=False
    )

    def __str__(self):
        return self.nickname


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


def post_image_path(instance: "Post", filename: str) -> str:
    _, extention = os.path.splitext(filename)
    filename = f"{slugify(instance.content[:10])}-{uuid.uuid4()}{extention}"
    return os.path.join("uploads/post/", filename)


class Post(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    image = models.ImageField(null=True, blank=True, upload_to=post_image_path)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True)

    @property
    def like_count(self):
        return self.likes.count()

    def __str__(self):
        return f"{self.author}: {self.content[:30]}"

    class Meta:
        ordering = ["-created_at"]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def like_count(self):
        return self.likes.count()

    def __str__(self):
        return f"{self.author}: {self.content[:30]}"

    class Meta:
        ordering = ["-created_at"]


class Like(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=True, blank=True, related_name="likes"
    )
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        unique_together = (("post", "author"),)


class Message(models.Model):
    author = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="received_messages"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"from {self.sender} to {self.recipient}: {self.content[:30]}"

    class Meta:
        ordering = ["-created_at"]
