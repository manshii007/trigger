#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import Permission
from django.contrib.auth import settings
import uuid

from content.models import (
    Movie,
    MovieSegment,
    Episode,
    EpisodeSegment
)
from workgroups.models import (
    WorkGroup
)
from tags.models import Tag
from video.models import Video
from frames.models import Frames

from users.models import (
    User
)


class JobType(models.Model):
    """
    Encapsulated the permissions associated with the job
    Type of Job
     |---> name
     |---> description
     |---> permissions [dynamic to content]
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=256, blank=True)
    permissions = models.ManyToManyField(Permission)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        permissions = (("view_jobtype", "Can view job type"),)


class Job(models.Model):
    """
    Job model description
    Job
     |---> id
     |---> created on time
     |---> modified on time
     |---> job description
     |---> due date
     |---> status
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # basic modification tracker
    # TODO implement all event tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    # due date can be blank
    due_date = models.DateField(null=True)

    job_status = models.CharField(max_length=3,
                                  choices=settings.JOB_STATUS,
                                  default='NPR'
                                  )
    priority = models.IntegerField(default=5)
    description = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        permissions = (("view_job", "Can view job"),)


class TaggingJob(Job):
    """
    TaggingJob model description
    TaggingJob
     |---> id
     |---> created on time
     |---> modified on time
     |---> job description
     |---> due date
     |---> status
     |---> created by (User)
     |---> assigned to (Workgroup)
     |---> activated by (User)
     |---> content (video | general content)
     |---> job type (what to be tagged)
    """
    created_in = models.ForeignKey(WorkGroup, related_name='tagging_jobs_assigned', null=True)
    created_by = models.ForeignKey(User, related_name='tagging_jobs_given')
    assigned_to = models.ForeignKey(WorkGroup, related_name='tagging_jobs')
    taken_by = models.ForeignKey(User, related_name='tagging_jobs_taken', null=True)
    video = models.ForeignKey(Video, blank=False)
    job_type = models.ForeignKey(JobType, blank=False)

    def __str__(self):
        return self.job_type.name + '_' + self.video.title

    def __unicode__(self):
        return self.job_type.name + '_' + self.video.title

    class Meta:
        permissions = (("view_taggingjob", "Can view tagging job"),)


class FrameJob(Job):
    assigned_to = models.ForeignKey(User, related_name='frame_jobs', blank=False)
    frame = models.ForeignKey(Frames, blank=False)
    tags = models.ManyToManyField(Tag, blank=False)

    def __str__(self):
        return str(self.frame.id) + "_" + str(self.id)

    def __unicode__(self):
        return str(self.frame.id) + "_" + str(self.id)


class AutoVideoJob(Job):
    created_by = models.ForeignKey(User, related_name='auto_video_jobs_given', null=True, blank=True)
    video = models.ForeignKey(Video, blank=False)
    job_type = models.ForeignKey(JobType, blank=False)
    eta = models.FloatField(null=True, blank=True, default=0)

    def __str__(self):
        return self.job_type.name + '_' + self.video.title

    def __unicode__(self):
        return self.job_type.name + '_' + self.video.title

    class Meta:
        permissions = (("view_autovideojob", "Can view auto video job"),)


class SubtitleSyncJob(Job):
    created_by = models.ForeignKey(User, related_name='subtitle_sync_jobs_given')
    audio_file = models.URLField()
    transcription = models.URLField()
    srt_file = models.URLField(null=True, blank=True)
    eta = models.FloatField(null=True, blank=True, default=0)
    percent_complete = models.IntegerField(null=True, blank=True, default=0)
    #  time taken for the job


class ScriptProcessJob(Job):
    created_by = models.ForeignKey(User, related_name='script_process_jobs_given')
    script_file = models.URLField()
    txt_file = models.URLField(null=True, blank=True)
    eta = models.FloatField(null=True, blank=True, default=0)
    percent_complete = models.IntegerField(null=True, blank=True, default=0)


class SubtitleTranslationJob(Job):
    Languages = (
        ('FR', 'French'),
        ('SP', 'Spanish'),
        ('EN', 'English'),
        ('HI', 'Hindi'),
    )
    created_by = models.ForeignKey(User, related_name='subtitle_translation_job_given', blank=False)
    video = models.ForeignKey(Video, blank=False)
    assigned_to = models.ForeignKey(User, related_name='subtitle_translation_job_assigned', blank=False)
    source_subtitle = models.URLField(null=True, blank=True)
    target_language = models.CharField(max_length=2, choices=Languages, default="EN")

    def __str__(self):
        return self.video.title

    def __unicode__(self):
        return self.video.title

    class Meta:
        permissions = (("view_subtitletranslationjob", "Can view subtitle translation job"),)


class ReviewTranslationJob(Job):
    Languages = (
        ('FR', 'French'),
        ('SP', 'Spanish'),
        ('EN', 'English'),
        ('HI', 'Hindi'),
    )
    created_by = models.ForeignKey(User, related_name='review_translation_job_given', blank=False)
    video = models.ForeignKey(Video, blank=False)
    assigned_to = models.ForeignKey(User, related_name='review_translation_job_assigned', blank=False)
    source_subtitle = models.URLField(null=True, blank=True)
    target_subtitle = models.URLField(null=True, blank=True)
    target_language = models.CharField(max_length=2, choices=Languages, default="EN")

    def __str__(self):
        return self.video.title

    def __unicode__(self):
        return self.video.title

    class Meta:
        permissions = (("view_reviewtranslationjob", "Can view review translation job"),)


class MovieTranslationJob(Job):
    Languages = (
        ('FR', 'French'),
        ('SP', 'Spanish'),
        ('EN', 'English'),
        ('HI', 'Hindi'),
    )
    created_by = models.ForeignKey(User, related_name='movie_translation_job_given', blank=False)
    assigned_to = models.ForeignKey(User, related_name='movie_translation_job_assigned', blank=False)
    movie = models.ForeignKey(Movie, blank=False)
    movie_segment = models.ForeignKey(MovieSegment, blank=True, null=True)
    source_subtitle = models.URLField(null=True, blank=True)
    target_subtitle = models.URLField(null=True, blank=True)
    target_language = models.CharField(max_length=2, choices=Languages, default="EN")

    def __str__(self):
        return self.movie.movie_title

    def __unicode__(self):
        return self.movie.movie_title

    class Meta:
        permissions = (("view_movietranslationjob", "Can view movie translation job"),)


class EpisodeTranslationJob(Job):
    Languages = (
        ('FR', 'French'),
        ('SP', 'Spanish'),
        ('EN', 'English'),
        ('HI', 'Hindi'),
    )
    created_by = models.ForeignKey(User, related_name='episode_translation_job_given', blank=False)
    assigned_to = models.ForeignKey(User, related_name='episode_translation_job_assigned', blank=False)
    episode = models.ForeignKey(Episode, blank=False)
    episode_segment = models.ForeignKey(EpisodeSegment, blank=True, null=True)
    source_subtitle = models.URLField(null=True, blank=True)
    target_subtitle = models.URLField(null=True, blank=True)
    target_language = models.CharField(max_length=2, choices=Languages, default="EN")

    def __str__(self):
        return self.episode.episode_title

    def __unicode__(self):
        return self.episode.episode_title

    class Meta:
        permissions = (("view_episodetranslationjob", "Can view episode translation job"),)