from django.urls import path, include
from rest_framework import routers

from social_media.views import (
    ProfileViewSet,
    PostViewSet,
    CommentViewSet,
    LikeViewSet,
    MessageViewSet,
)


router = routers.DefaultRouter()
router.register("profiles", ProfileViewSet)
router.register("posts", PostViewSet)
router.register("comments", CommentViewSet)
router.register("likes", LikeViewSet)
router.register("messages", MessageViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "social_media"
