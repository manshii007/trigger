#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.mail import send_mail, EmailMessage
from video.serializers import CreateVideoSerializer
from tags.models import FrameTag, KeywordTag, CheckTag, CorrectionTag, EmotionTag
from .models import TaggingJob, AutoVideoJob, JobType, SubtitleSyncJob
from .tasks import set_frame_tags, subtitle_sync
import logging
from guardian.shortcuts import assign_perm

from video.tasks import (
    background_video_processing_aws_objects,
    background_video_processing_aws_emotions,
    background_nudity_video,
    background_compliance_video,
    background_compliance_audio,
    background_video_processing,
    background_rolling_credit,
    background_video_processing_trivia,
    background_video_processing_face_detection,
    backgroudprocess_match_face,
    backgroundprocess_keywords,
    background_detect_text,
    backgroundprocess_emotion,
    backgroundprocess_sentiment,
    background_video_processing_hardcuts,
    background_detect_text,
    background_location_video,
    background_logo_video,
    background_drugs_video,
    background_smoke_video,
    background_alcohol_video,
    background_fire_video,
    background_sexdolls_video,
    background_flag_video,
    background_statue_video
)
import os, uuid
logger = logging.getLogger('debug')


@receiver(post_save, sender=TaggingJob)
def process_for_tags(sender, instance, **kwargs):
    """
    Call get_metadata on_save
    :param sender:
    :param kwargs:
    :return:
    """
    if kwargs.get('created'):
        # Tagging Job instance is just created, get the video id and pass it to GRPC backend
        video_instance = instance.video
        assign_perm('view_video', instance.taken_by, instance)
        assign_perm('view_video', instance.created_by, instance)


@receiver(post_save, sender=AutoVideoJob)
def process_for_tags(sender, instance, **kwargs):
    if kwargs.get('created'):
        logger.debug('We are here')
        logger.debug(instance.job_type.name)
        video_instance = instance.video

        email = EmailMessage(
            'File processing Update',
            "{} is scheduled for {} processing".format(video_instance.title, instance.job_type.name),
            'aswin@tessact.com',
            ['aswin@tessact.com']
        )
        #append this to tasks downloading tmp video file. Incase of failure of task we need to delete the video downloaded
        # and will provide a path to the same.
        tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4())+'.mp4') 

        if instance.job_type.name == 'Compliance':
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Compliance").delete()
            KeywordTag.objects.filter(video=video_instance, created_by=None, tags__name__iexact="Profanity").delete()
            background_compliance_video.delay(video_instance.file, video_instance.id, instance.id)
            background_compliance_audio.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Compliance Audio':
            KeywordTag.objects.filter(video=video_instance, created_by=None, tags__name__iexact="Profanity").delete()
            background_compliance_audio.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Detect Nudity':
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Nudity").delete()
            CheckTag.objects.filter(video=video_instance, created_by=None, autotag__parent__title__iexact="Nudity").delete()
            background_nudity_video.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Identify Drugs':
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Drugs").delete()
            CheckTag.objects.filter(video=video_instance, created_by=None, autotag__parent__title__iexact="Drugs").delete()
            background_drugs_video.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Identify Smoking':
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Smoking").delete()
            CheckTag.objects.filter(video=video_instance, created_by=None, autotag__parent__title__iexact="Smoking").delete()
            background_smoke_video.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Identify Alcohol':
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Alcohol").delete()
            CheckTag.objects.filter(video=video_instance, created_by=None, autotag__parent__title__iexact="Alcohol").delete()
            background_alcohol_video.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Identify Fire':
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Fire").delete()
            CheckTag.objects.filter(video=video_instance, created_by=None, autotag__parent__title__iexact="Fire").delete()
            background_fire_video.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Identify Sex Dolls':
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Sex Dolls").delete()
            CheckTag.objects.filter(video=video_instance, created_by=None, autotag__parent__title__iexact="Sex Dolls").delete()
            background_sexdolls_video.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Identify Indian Flag':
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Indian Flag").delete()
            CheckTag.objects.filter(video=video_instance, created_by=None, autotag__parent__title__iexact="Indian Flag").delete()
            background_flag_video.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Identify Naked Statue':
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Naked Statue").delete()
            CheckTag.objects.filter(video=video_instance, created_by=None, autotag__parent__title__iexact="Naked Statue").delete()
            background_statue_video.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Identify Locations':
            logger.debug('we are starting clearing')
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Locations").delete()
            background_location_video.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Identify Objects':
            logger.debug('we are starting clearing')
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Others").delete()
            background_video_processing.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name)

        if instance.job_type.name == 'Identify Logos':
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Logo").delete()
            background_logo_video.delay(video_instance.file, video_instance.id, instance.id)

        elif instance.job_type.name == 'Identify Faces' :
            background_video_processing_face_detection.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name)

        elif instance.job_type.name == "Identify Emotion":
            backgroundprocess_emotion.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name)

        elif instance.job_type.name == "Identify Emotion AWS":
            EmotionTag.objects.filter(video=video_instance).delete()
            background_video_processing_aws_emotions.delay(video_instance.file, video_instance.id, instance.id)

        if instance.job_type.name == 'Identify Objects AWS':
            FrameTag.objects.filter(video=video_instance, created_by=None, tag__parent__title__iexact="Others").delete()
            background_video_processing_aws_objects.delay(video_instance.file, video_instance.id, instance.id)

        elif instance.job_type.name == 'Identify Trivia':
            background_video_processing_trivia.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name)

        elif instance.job_type.name == 'Match Faces':
            backgroudprocess_match_face.delay(video_instance.id, instance.id)

        elif instance.job_type.name == 'Find Keywords Hindi':
            backgroundprocess_keywords.delay(video_instance.file, video_instance.id, instance.id, 'hi-IN', tmp_file_name)

        elif instance.job_type.name == 'Find Keywords English With Sentiment':
            backgroundprocess_sentiment.delay(video_instance.file, video_instance.id, instance.id, 'en-IN', tmp_file_name)

        elif instance.job_type.name == 'Find Keywords Hindi With Sentiment':
            backgroundprocess_sentiment.delay(video_instance.file, video_instance.id, instance.id, 'hi-IN', tmp_file_name)

        elif instance.job_type.name == 'Find Keywords Marathi With Sentiment':
            backgroundprocess_sentiment.delay(video_instance.file, video_instance.id, instance.id, 'mr-IN', tmp_file_name)

        elif instance.job_type.name == 'Generate Hardcuts':
            background_video_processing_hardcuts.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name)

        elif instance.job_type.name == 'Find Keywords':
            backgroundprocess_keywords.delay(video_instance.file, video_instance.id, instance.id, 'en-US', tmp_file_name)

        elif instance.job_type.name == "Detect Text":
            background_detect_text.delay(video_instance.file, video_instance.id, instance.id, None, None, 'en', tmp_file_name, tmp_file_name=tmp_file_name)

        else:
            pass


@receiver(post_save, sender=SubtitleSyncJob)
def process_for_sync(sender, instance, **kwargs):
    if kwargs.get('created'):
        logger.debug('Sync job started')
        subtitle_sync.delay(str(instance.id))

