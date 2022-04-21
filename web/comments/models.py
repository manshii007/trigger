from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import User

import uuid


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, blank=True, null=True)
    submit_datetime = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    comment = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    is_removed = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        permissions = (
                    ("user_view_comment", "User level can view comment"),("team_view_comment", "Team level can view comment"), ("org_view_comment", "Org level can view comment"),
                    ("user_add_comment", "User level can add comment"),("team_add_comment", "Team level can add comment"), ("org_add_comment", "Org level can add comment"),
                    ("user_change_comment", "User level can change comment"),("team_change_comment", "Team level can change comment"), ("org_change_comment", "Org level can change comment"),
                    ("user_delete_comment", "User level can delete comment"),("team_delete_comment", "Team level can delete comment"), ("org_delete_comment", "Org level can delete comment"),
                )