#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.dispatch import receiver
from django.db import models
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
import datetime
from content.models import ChannelClip
from content.tasks import get_tag_fprints
from datetime import datetime, timedelta

from .models import ContentLanguage, ProductionHouse, ProgramGenre, ProgramTheme, FrameTag, Tag, \
    TagCategory, PlayoutTag, Title, Descriptor, BrandName, BrandCategory, BrandSector, Advertiser, \
    AdvertiserGroup, ChannelGenre, ChannelNetwork, Channel, Region, PromoCategory, GenericTag, ManualTag, \
    ManualTagQCStatus

from video.models import Video
from contextual.models import HardCuts

import logging, sys

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO'
    }
}
logging.config.dictConfig(LOGGING)

@receiver(post_save, sender=Tag)
@receiver(post_delete, sender=Tag)
def tag_api_updated_at(**kwargs):
    cache.set('tag_api_updated_at_timestamp', datetime.utcnow())


@receiver(post_save, sender=TagCategory)
@receiver(post_delete, sender=TagCategory)
def tag_category_api_updated_at(**kwargs):
    cache.set('tag_category_api_updated_at_timestamp', datetime.utcnow())


@receiver(post_save, sender=FrameTag)
@receiver(post_delete, sender=FrameTag)
def frame_tag_api_updated_at(**kwargs):
    cache.set('frame_tag_api_updated_at_timestamp', datetime.utcnow())


@receiver(post_save, sender=PlayoutTag)
def playout_tag_created(sender, instance, **kwargs):
    try:
        if kwargs.get('created'):
            # print("playout tag created, update the filled duration")
            p = PlayoutTag.objects.filter(video=instance.video).order_by('frame_in')
            d = int(instance.video.duration)
            hit_list = [0]*d
            for ptag in p:
                t1 = int(ptag._time_in_sec() if ptag._time_in_sec()>0  else 0)
                t2 = int(ptag._time_out_sec() if ptag._time_out_sec()< d else d)
                for t in range(t1, t2):
                    hit_list[t] += 1
            channel_clip = ChannelClip.objects.filter(video=instance.video)
            if channel_clip:
                tmp = channel_clip.first()
                tmp.filled_duration = int(sum(x>0 for x in hit_list))
                tmp.save()
    except ValueError or IndexError :
        pass


@receiver(post_save, sender=PlayoutTag)
def playout_tag_created_fprint(sender, instance, **kwargs):
    try:
        if kwargs.get('created'):
            # print("playout tag created, update the filled duration")
            if instance.content_type=="commercial" or instance.content_type=="promo":
                vid = ChannelClip.objects.filter(video=instance.video).first()
                if vid:
                    dt = vid.date.__str__()
                    yy = int(dt.split("-")[0])
                    mm = int(dt.split("-")[1])
                    dd = int(dt.split("-")[2])
                    start_datetime = datetime(year=yy, month=mm, day=dd) + timedelta(hours=2)
                    pt = PlayoutTag.objects.filter(video__channelclip__start_time__gte=start_datetime,
                                                   video__channelclip__start_time__lte=vid.start_time,
                                                   video__channelclip__channel__channel_code=vid.channel.channel_code,
                                                   object_id=instance.object_id).count()
                    if pt==1:
                        get_tag_fprints.delay(instance.id)
    except ValueError or IndexError :
        pass


@receiver(post_save, sender=GenericTag)
def add_colors(sender, instance, **kwargs):
    if kwargs.get("created"):
        # logging.info(instance)
        if instance.level is 2:
            top_parent = GenericTag.objects.filter(id=instance.parent.parent.id).first()
            #Create Colors only for tags whose parent at level 0 is Objects
            if top_parent.title == "Objects":
                arr = ["Red", "Yellow", "Green", "Blue", "Black", "White", "Orange", "Violet", "Pink", "Brown", "Grey", "None"]
                obj_list = []
                
                for title in arr:
                    obj = GenericTag.objects.create(title=title, parent=instance)          

@receiver(post_save, sender=HardCuts)
def generate_frame_tag(sender, instance, **kwargs):
    if kwargs.get("created"):
        video_instance = instance.video
        frame_rate = video_instance.frame_rate
        hardcuts_list = instance.cuts

        obj_list =[]

        for cut in hardcuts_list:
            obj = ManualTag(frame_in = cut[0]*frame_rate, frame_out = cut[1]*frame_rate,
                            video = video_instance)
            obj_list.append(obj)

        ManualTag.objects.bulk_create(obj_list)

# @receiver(post_save, sender=ManualTag)
# def generate_manual_tag_qc_status(sender, instance, **kwargs):

#     #Create QC status entry for every generic tag added to a manual tag
#     if kwargs.get("created") == False:
#         existing_manual_tags_qc_qs = ManualTagQCStatus.objects.filter(manual_tag=instance)
#         for tag in instance.tags.all():
#             # if the tag exists in manual_tag_qc_status model keep it as is.
#             if existing_manual_tags_qc_qs.filter(tag=tag).exists():
#                 existing_manual_tags_qc_qs = existing_manual_tags_qc_qs.exclude(tag=tag)
#             else:
#                 ManualTagQCStatus.objects.create(tag=tag, manual_tag=instance, qc_approved=True)
        
#         # remove the manual_tag_qc_status entry if the tag is removed  from manual tag.     
#         if len(existing_manual_tags_qc_qs) > 0:
#             existing_manual_tags_qc_qs.delete()

# @receiver(post_save, sender=Descriptor)
# def descriptor_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = Descriptor.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()


# @receiver(post_save, sender=ContentLanguage)
# def lang_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = ContentLanguage.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()
#
#
# @receiver(post_save, sender=ProgramGenre)
# def genre_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = ProgramGenre.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()
#
#
# @receiver(post_save, sender=ProgramTheme)
# def theme_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = ProgramTheme.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()


# @receiver(post_save, sender=BrandName)
# def brand_name_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = BrandName.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()
#
#
# @receiver(post_save, sender=BrandSector)
# def brand_sector_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = BrandSector.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()
#
#
# @receiver(post_save, sender=BrandCategory)
# def brand_category_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = BrandCategory.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()
#
#
# @receiver(post_save, sender=Advertiser)
# def advertiser_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = Advertiser.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()
#
#
# @receiver(post_save, sender=AdvertiserGroup)
# def advertiser_group_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = AdvertiserGroup.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()
#
#
# @receiver(post_save, sender=ProductionHouse)
# def production_house_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = ProductionHouse.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()


# @receiver(post_save, sender=Channel)
# def channel_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = Channel.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()
#
#
# @receiver(post_save, sender=ChannelNetwork)
# def channel_network_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = ChannelNetwork.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()


# @receiver(post_save, sender=ChannelGenre)
# def channel_genre_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = ChannelGenre.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()


# @receiver(post_save, sender=PromoCategory)
# def promo_category_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = PromoCategory.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()


# @receiver(post_save, sender=Region)
# def region_created(sender, instance, **kwargs):
#     if kwargs.get("created"):
#         max_code = Region.objects.filter(code__isnull=False).order_by('-code').first().code
#         instance.code = max_code + 1
#         instance.save()