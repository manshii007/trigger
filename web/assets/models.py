from django.db import models
import uuid
from users.models import User


class RO(models.Model):
    PROCESS_STATUS = (
        ('CMP', 'Completed'),
        ('ERR', 'Error'),
        ('NPR', 'Not Processed'),
        ('PRO', 'Processing')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_file = models.URLField(blank=True, null=True)
    final_file = models.URLField(blank=True, null=True)
    channel = models.CharField(max_length=128, null=True)
    object = models.CharField(max_length=128, null=True)
    dest = models.CharField(max_length=128, null=True)
    advertiser = models.CharField(max_length=128, null=True)
    brand = models.CharField(max_length=128, null=True)
    ronumber = models.CharField(max_length=128, null=True)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    created_by = models.ForeignKey(User, null=True, blank=True)

    title = models.CharField(max_length=256, null=True, blank=True)

    process_status = models.CharField(choices=PROCESS_STATUS, max_length=3, default='NPR', null=True)
    process_eta = models.FloatField(null=True, default=0.0)

    def __str__(self):
        return str(self.id)

    class Meta:
        permissions = (("view_ro", "Can view ro"),)
        ordering = ['-created_on']