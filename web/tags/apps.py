#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.apps import AppConfig


class TagsConfig(AppConfig):
    name = 'tags'

    def ready(self):
        import tags.signals
