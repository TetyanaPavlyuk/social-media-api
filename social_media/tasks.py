from celery import shared_task

from .models import Post


@shared_task
def publish_scheduled_posts(post_id):
    try:
        post = Post.objects.get(id=post_id)
        post.is_published = True
        post.save()
    except Post.DoesNotExist as e:
        raise e
