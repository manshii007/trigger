#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from __future__ import absolute_import, unicode_literals


# default_app_config = 'trigger.apps.TriggerConfig'

from .celery import app as celery_app

__all__ = ['celery_app']
