#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_img_file_type(upload):
    if not upload.name.split('.')[-1].lower() in settings.IMG_TYPES:
        raise ValidationError('File type not supported')
