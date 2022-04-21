from django.dispatch import receiver
from django.db import models
from django.db.models.signals import post_save, post_delete

from .models import Comment
from tags.models import FrameTag
from users.models import User
from content.models import AssetVersion
from notifications.signals import notify

def send_notification(instance, action):
	obj = instance.content_object
	obj_model = str(obj._meta.model.__name__)
	# place a check for the frametags if required
	if obj_model = 'FrameTag':
		users_list = Comment.objects.filter(object_id=obj.id).values_list('user', flat=True)
		users_all = list(User.objects.filter(id__in=users_list))
		asset_title = AssetVersion.objects.filter(video=obj.video).first().title
		notifications = notify.send(sender=sender, recipient=users_all, verb='<b>{} {}</b> {} comment on <b>{}</b>'.format(sender.first_name, sender.last_name, action, asset_title))
	else:
		return

@receiveras(post_save, sender=Comment)
def notify_users(sender, instance, **kwargs):
	if kwargs.get("created"):
		send_notification(instance, "added")
	else:
		end_notification(instance, "edited")

@receiver(post_delete, sender=Comment)
def notify_users_on_delete(sender, instance, **kwargs):
	send_notification(instance, "deleted")





