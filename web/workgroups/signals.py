#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.dispatch import receiver
from django.db import models
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
import datetime
from .models import WorkGroup, Group


@receiver(post_delete, sender=WorkGroup)
@receiver(post_save, sender=WorkGroup)
@receiver(post_save, sender=Group)
@receiver(post_delete, sender=Group)
def change_api_updated_at(**kwargs):
    cache.set('workgroup_api_updated_at_timestamp', datetime.datetime.utcnow())