#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.apps import AppConfig


class VideoConfig(AppConfig):
    name = 'video'

    def ready(self):
        import video.signals
        import video.tasks
