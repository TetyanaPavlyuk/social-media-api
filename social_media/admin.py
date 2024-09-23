from django.contrib import admin

from social_media.models import Profile, Post, Comment, Like, Message, Tag


admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Message)
admin.site.register(Tag)
