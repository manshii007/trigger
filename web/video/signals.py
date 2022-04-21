#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.dispatch import receiver
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from versatileimagefield.image_warmer import VersatileImageFieldWarmer
from utils.azure_storage import AzureStorage
import datetime

from .models import Video
from jobs.models import JobType, AutoVideoJob
from users.models import User
from .serializers import CreateVideoSerializer
from .tasks import set_metadata, background_video_processing, background_video_processing_hardcuts, set_hardcuts, create_sprites, process_for_emotion, process_for_face_detect


@receiver(post_save, sender=Video)
def process_metadata(sender, instance, **kwargs):
    """Call get_metadata on_save"""
    if kwargs.get('created') :
        video_serializer = CreateVideoSerializer(instance, partial=True)
        video_file=video_serializer.data['file']
        task_id = set_metadata.delay(video_file, video_serializer.data['id'])
        task_id = set_hardcuts.delay(video_file, video_serializer.data['id'])
        create_sprites.delay(video_file, video_serializer.data['id'])
        process_for_emotion.delay(video_serializer.data['id'])
        process_for_face_detect.delay(video_serializer.data['id'])
        # process_service = background_video_processing.delay(video_file, video_serializer.data['id'])


@receiver(post_delete, sender=Video)
def delete_video_file_resources(sender, instance, **kwargs):
    """call the filefield delete method after post_delete is broadcasted"""
    storage_instance = AzureStorage()
    blob_name = ''.join(instance.file.split('/')[4:])
    storage_instance.delete(blob_name)


@receiver(post_delete, sender=Video)
@receiver(post_save, sender=Video)
def video_api_update_at(**kwargs):
    cache.set('video_api_updated_at_timestamp', datetime.datetime.utcnow())


@receiver(post_save, sender=Video)
def warm_video_poster_images(sender, instance, **kwargs):
    """Ensure Video Poster images are created post-save"""
    video_poster_warmer = VersatileImageFieldWarmer(
        instance_or_queryset=instance,
        rendition_key_set='video_poster',
        image_attr='poster',
    )
    num_created, failed_to_create = video_poster_warmer.warm()



# @receiver(post_save, sender=Video)
# def process_hardcuts(sender, instance, **kwargs):
#     """Ensures hardcuts are created post-save"""
#     if kwargs.get('created') :
#         video_serializer = CreateVideoSerializer(instance, partial=True)
#         video_file=video_serializer.data['file']
#         task_id = background_video_processing_hardcuts.delay(video_file, video_serializer.data['id'])

# @receiver(post_save, sender=Video)
# def process_for_face_detection(sender, instance, **kwargs):
#     """Ensures face-detection are created post-save"""
#     if kwargs.get('created') :
#         job_type_instance_identify_faces, _ = JobType.objects.get_or_create(name='Identify Faces')
#         job_type_instance_match_faces, _ = JobType.objects.get_or_create(name='Match Faces')
#         u = User.objects.get(username='test_user')
        
#         auto_identify_faces = AutoVideoJob.objects.create(created_by=u, video=instance, job_type=job_type_instance_identify_faces, eta=0)
#         auto_match_faces = AutoVideoJob.objects.create(created_by=u, video=instance, job_type=job_type_instance_match_faces, eta=0)

# @receiver(post_save, sender=Video)
# def process_for_face_macthing(sender, instance, **kwargs):
#     """Ensures face-detection are created post-save"""
#     if kwargs.get('created') :
#         job_type_instance, _ = JobType.objects.get_or_create(name='Match Faces')
#         u = User.objects.get(username='test_user')
#         auto = AutoVideoJob.objects.create(created_by=u, video=instance, job_type=job_type_instance, eta=0)









    
