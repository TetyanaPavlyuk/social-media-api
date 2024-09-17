import os
import uuid

from django.db import models
from django.utils.text import slugify

from user.models import User


def profile_image_path(instance: "Profile", filename: str) -> str:
    _, extention = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extention}"
    return os.path.join("uploads/profile/", filename)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    nickname = models.CharField(max_length=255)
    photo = models.ImageField(null=True, blank=True, upload_to=profile_image_path)
    birth_date = models.DateField(null=True, blank=True)
    following = models.ManyToManyField(
        "self", related_name="followers", symmetrical=False, null=True, blank=True
    )

    def __str__(self):
        return self.nickname


def post_image_path(instance: "Post", filename: str) -> str:
    _, extention = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extention}"
    return os.path.join("uploads/post/", filename)


class Post(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    image = models.ImageField(null=True, blank=True, upload_to=post_image_path)
    created_at = models.DateTimeField(auto_now_add=True)

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
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, null=True, blank=True, related_name="likes"
    )
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="likes")


class Message(models.Model):
    sender = models.ForeignKey(
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
