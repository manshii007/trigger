#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
import uuid
import content
from users.models import User
from django.apps import apps
# from content.models import AssetVersion
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from versatileimagefield.fields import VersatileImageField, PPOIField
from versatileimagefield.placeholder import OnStoragePlaceholderImage
from django.contrib.postgres.fields import ArrayField, JSONField
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
import datetime
from math import floor
from .validator import validate_video_file_type

from utils.unique_filename import unique_upload
from thumbnails.models import Thumbnail

class VideoProxyPath(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    processing_status_choices_nbm = (
        ('QUE', 'Queued'),
        ('PRD', 'Processed'),
        ('PRO', 'Processing'),
        ('FAI', 'Failed')
    )

    storage_status_choices = (
        ('NPR', 'Not Processed'),
        ('ONL', 'Online'),
        ('ARC', 'Archived'),
        ('ALL', 'Online & Archived')
    )

    processing_status_choices_proxy = (
        ('NPR', 'Not Processed'),
        ('QUE', 'Queued'),
        ('PRD', 'Processed'),
        ('PRO', 'Processing'),
        ('FAI', 'Failed')
    )

    upload_status_choices_proxy = (
        ('NST', 'Uploading not Started'),
        ('UPL', 'Uploading'),
        ('UPD', 'Sucessfully Uploaded'),
        ('FAI', 'Uploading Failed'),
    )

    title = models.CharField(max_length=1024, verbose_name="Name")
    file = models.CharField(max_length=1024, blank=True, null=True)
    metadata = models.TextField(blank=True, null=True)

    nbm = models.TextField(max_length=1024, blank=True, null=True)
    nbm_processing_status = models.CharField(max_length=3, choices=processing_status_choices_nbm, default='QUE',
                                                null=True, blank=True)
    nbm_storage_status = models.CharField(max_length=3, choices=storage_status_choices, default='NPR', 
                                                null=True, blank=True)
    nbm_progress = models.PositiveIntegerField(default=0, null=True)

    sourceproxy = models.CharField(max_length=1024, blank=True, null=True)
    sourceproxy_processing_status = models.CharField(max_length=3, choices=processing_status_choices_proxy,
                                                        default='NPR', null=True, blank=True)
    
    sourceproxy_progress = models.PositiveIntegerField(default=0, null=True)

    sourceproxy_upload_progress = models.PositiveIntegerField(default=0, null=True)
    sourceproxy_upload_status = models.CharField(max_length=3, choices=upload_status_choices_proxy,
                                                    default='NST', null=True, blank=True)

    # ingest_date = models.DateField(null=True, blank=True)
    # master = models.CharField(max_length=1024, blank=True, null=True)

    # intermediate = ArrayField(models.CharField(max_length=1024), blank=True, null=True)
    #####Adding technical metadat feilds for NBM######
    duration = models.FloatField(default=0)
    height = models.PositiveIntegerField(null=True)
    width = models.PositiveIntegerField(null=True)
    frame_rate = models.FloatField(null=True)
    video_codec = models.CharField(max_length=128, null=True)
    total_frames = models.PositiveIntegerField(null=True)
    bitrate = models.PositiveIntegerField(null=True)
    size = models.FloatField(default=0, null=True, blank=True)

    ##Techincal Matatata for audio
    audio_codec = models.CharField(max_length=128, null=True)
    audio_bitrate = models.PositiveIntegerField(null=True)
    audio_sample_rate = models.PositiveIntegerField(null=True)
    audio_tracks_no = models.PositiveIntegerField(null=True)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.id)

@python_2_unicode_compatible
class Video(models.Model):
    """
    video model consist of all base features of a Media content
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=128, verbose_name="Title")

    # File Type Validation done in validator.py
    # file = models.FileField(upload_to=unique_upload, max_length=None, validators=[validate_video_file_type])
    file = models.URLField()
    # No object can be deleted, only action allowed is to set it inactive
    is_removed = models.BooleanField(default=False)

    # basic modification tracker
    # TODO implement all event tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    duration = models.FloatField(default=0)
    height = models.PositiveIntegerField(null=True)
    width = models.PositiveIntegerField(null=True)
    frame_rate = models.FloatField(null=True)
    video_codec = models.CharField(max_length=128, null=True)
    total_frames = models.PositiveIntegerField(null=True)
    bitrate = models.PositiveIntegerField(null=True)
    size = models.FloatField(default=0, null=True, blank=True)

    created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL)

    metadata = models.OneToOneField(VideoProxyPath, on_delete=models.SET_NULL, null=True,
                                            blank=True)
    picture = models.URLField(null=True, blank=False)
    thumbnail = GenericRelation(Thumbnail, related_query_name='thumbnail')
    aws_face_json = JSONField(null=True, blank=True)
    aws_object_json = JSONField(null=True, blank=True)
    is_nft = models.BooleanField(default=False)
    
    # Thumbnail
    poster = VersatileImageField(
        'Poster',
        upload_to=unique_upload,
        ppoi_field='poster_ppoi',
        blank=True,
        null=True,
        placeholder_image=OnStoragePlaceholderImage(
            path='No_picture_available.png'
        )
    )

    poster_ppoi = PPOIField()

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title

    def _readable_duration(self):
        """Returns duration in readable format"""
        base_time = str(datetime.timedelta(seconds=floor(self.duration)))
        return base_time

    def poster_img(self):
        if self.poster:
            return u'<img src="%s" />' % self.poster.thumbnail['100x100'].url

    poster_img.short_description = 'Poster'
    poster_img.allow_tags = True

    def video_player(self):
        if self.file:
            return u'<video width="320" height="240" controls autoplay><source src="%s" type="video/mp4"> Your browser does not support the video tag.</video>' % self.file

    video_player.short_description = 'Video'
    video_player.allow_tags = True

    class Meta:
        permissions = (("view_video", "Can view video"),)
        ordering = ['-created_on']


class VideoLibrary(models.Model):
    """
    Library for each Workgroup.
    Library
    |---> id
    |---> Video
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    videos = models.ManyToManyField(Video)

    class Meta:
        verbose_name_plural = 'Libraries'


class Audio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.URLField()

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    # audio  metadata
    duration = models.FloatField(default=0)
    audio_codec = models.CharField(max_length=128, null=True)

    def __unicode__(self):
        return str(self.id)

    def __str__(self):
        return str(self.id)

    def _readable_duration(self):
        """Returns duration in readable format"""
        base_time = str(datetime.timedelta(seconds=floor(self.duration)))
        return base_time

    class Meta:
        permissions = (("view_audio", "Can view audio"),)


class Transcription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.URLField()

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __unicode__(self):
        return str(self.id)

    def __str__(self):
        return str(self.id)

    class Meta:
        permissions = (("view_transcription", "Can view transcription"),)


class Subtitle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.URLField()
    asset_version = models.ForeignKey('content.AssetVersion',null= True,  on_delete=models.CASCADE)
	
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    language = models.CharField(max_length=128, default='english')
    def __unicode__(self):
        return str(self.id)

    def __str__(self):
        return str(self.id)

    class Meta:
        permissions = (("view_subtitle", "Can view subtitle"),)


class VideoSubtitle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    subtitle = models.ForeignKey(Subtitle, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)

    def __str__(self):
        return self.title

    def __unicode__(self):
        return self.title

    class Meta:
        permissions = (("view_videosubtitle", "Can view video subtitle"),)

class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_ref = models.UUIDField(null=True, blank=True)
    project = models.TextField(blank=True, null=True)
    status = (
        ('PREPARING', 'Preparing'), 
        ('WAIT FOR JOB', 'Queued'), 
        ('PROCESSING', 'Processing'), 
        ('PROCESSED ', 'Processed'),
        ('DONE', 'Done') 
    )
    status = models.CharField(max_length=15, choices=status, default='PREPARING', null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.id)

class Clip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clip_ref = models.UUIDField(null=True, blank=True)
    status = (
        ('NOT STARTED', 'Queued'), #Not processed yet
        ('PROCESSING', 'Processing'), #Not a state in SDNA doc bt implemented to show which files 
                                        #currently being processed
        ('SUCCESS', 'Success'), #successfully archived
        ('EXISITS', 'Archived'), #Clip already archived
        ('FAILED', 'Failed') #Transfer failed.
    )
    ticket = models.ForeignKey(Ticket, null=True, blank=False, on_delete=models.CASCADE)    
    video_proxy_path = models.ForeignKey(VideoProxyPath, null=True, blank=False, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=status, default='NOT STARTED', null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.id)
