#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
import uuid
from django.conf import settings


def unique_upload(instance, filename):
    ext = filename.split('.').pop()
    if ext in settings.VIDEO_TYPES:
        return "{}.{}".format(uuid.uuid4(), ext)
    elif ext in settings.IMG_TYPES:
        return "{}.{}".format(uuid.uuid4(), ext)
