import uuid
from django.db import models
from users.models import User

class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, null=True, blank=True)
    user_feedback = models.TextField(null=True)
    report_issue = models.TextField(null=True)

    # basic modification tracker
    # TODO implement all event tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.id

    def __unicode__(self):
        return self.id

    class Meta:
        permissions = (("view_feedback", "Can view feedback item"),)
