#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.contrib import admin
from admin import admin_site
from .models import (
    TaggingJob,
    FrameJob,
    JobType,
    AutoVideoJob,
    SubtitleSyncJob,
    ScriptProcessJob
)

admin.site.register(TaggingJob)
admin.site.register(FrameJob)
admin.site.register(JobType)
admin.site.register(AutoVideoJob)
admin.site.register(SubtitleSyncJob)


class ScriptProcessAdmin(admin.ModelAdmin):
    pass

admin.site.register(ScriptProcessJob, ScriptProcessAdmin)