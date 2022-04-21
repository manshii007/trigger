from django.db import models
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import User

import uuid

# Create your models here.
class Thumbnail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    url = models.URLField(null=True, blank=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        permissions = (("view_thumbnail", "Can view thumbnail"),)