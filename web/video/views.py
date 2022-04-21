#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from rest_framework import viewsets, mixins, reverse
from rest_framework.response import Response
from django.core.mail import send_mail, EmailMessage
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import detail_route, list_route, api_view
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from rest_framework.views import APIView
from rest_framework_extensions.key_constructor.bits import (
    KeyBitBase,
    ListSqlQueryKeyBit,
    RetrieveSqlQueryKeyBit,
    PaginationKeyBit,
    UserKeyBit
)
from operator import itemgetter
import base64
import hashlib
import hmac
import time
from .file_upload_aws import (
    AWS_UPLOAD_BUCKET,
    AWS_UPLOAD_REGION,
    AWS_UPLOAD_ACCESS_KEY_ID,
    AWS_UPLOAD_SECRET_KEY
)
import logging
import csv
import uuid
import pandas as pd
import math, os
import re
import json
import operator
from google.cloud import speech, vision
from google.cloud.vision import types
from indic_transliteration import sanscript
from indic_transliteration.sanscript import SchemeMap, SCHEMES, transliterate
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils.encoding import force_text
from django.core.cache import cache
from django.contrib.postgres.search import SearchQuery
from django.conf import settings
from django.db.models import Q, F
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.postgres.aggregates import StringAgg
from functools import reduce
import django_filters
from guardian.shortcuts import get_objects_for_user
from rest_framework_extensions.mixins import CacheResponseMixin
from rest_framework import filters
from permissions.permissions import CustomObjectPermission, CustomDjangoModelPermission
from tags.models import FrameTag, KeywordTag, OCRTag
from tags.serializers import KeywordTagSerializer, OCRTagSerializer, ManualTagSerializer, MasterReportGenSerializer
from io import BytesIO
from utils.printing import PrintFrameTags, SonyReport, NX_report
from utils.db.postgres.headline import Headline
from azure.storage.blob import (
    BlockBlobService,
    BlobPermissions
)
from datetime import timedelta, datetime
from tags.serializers import (
    FrameTagSerializer,
    LogoTagSerializer
)
from comments.models import Comment
from tags.models import (
    Logo,
    LogoTag

)
from jobs.models import AutoVideoJob, JobType
from jobs.serializers import AutoVideoJobSerializer
from .tasks import (
    email_keywords_excel,
    email_keywords_reportlab,
    get_display_images_link,
    s3_signed_url,
    get_s3_signed_url,
    set_metadata,
    background_video_processing_hardcuts,
    background_rolling_credit,
    background_detect_text,
    backgroundprocess_keywords,
    merge_object_detections,
    background_video_processing_logo,
    background_video_processing_samosa,
    send_moderation_report,
    send_ingest_report,
    generate_edl,
    generate_search_edl,
    create_all_endpoints,
    delete_all_endpoints,
    compliance_tags,
    set_thumbnail
)
from contextual.models import FaceGroup, Face, VideoFrame, HardCuts
from contextual.serializers import FaceGroupSerializer, HardCutsSerializer
from .models import (
    Video,
    VideoLibrary,
    Audio,
    Transcription,
    Subtitle,
    VideoSubtitle,
    VideoProxyPath,
    Clip,
    Ticket,
)

from .serializers import (
    CreateVideoSerializer,
    VideoSerializer,
    DetailVideoSerializer,
    VideoLibrarySerializer,
    AudioSerializer,
    TranscriptionSerializer,
    SubtitleSerializer,
    SearchVideoSerializer,
    SearchVideoWithoutMatchSerializer,
    VideoSubtitleSerializer,
    CreateVideoSubtitleSerializer,
    DetailVideoSubtitleSerializer,
    VideoProxyPathSerializer,
    ClipSerializer,
    TicketSerializer,
)
from content.models import Credit, AssetVersion
from .filters import VideoFilter
import random
import codecs, requests
from tags.models import ComplianceStatusTag, MasterReportGen
import zipfile
import logging, sys
from publication.tasks import get_latest_publication, is_blacklisted
import urllib.parse

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
User = get_user_model()  # get user model from settings


def sec2TCR(t, fps):
    return (str(timedelta(seconds=math.floor(t)))+":"+(str(int(t*fps) - math.floor(fps*math.floor(t))).zfill(2))).zfill(11)

# cache testing
class VideoUpdatedAtKeyBit(KeyBitBase):
    def get_data(self, **kwargs):
        key = 'video_api_updated_at_timestamp'
        value = cache.get(key, None)
        if not value:
            value = datetime.utcnow()
            cache.set(key, value=value)
        return force_text(value)


class CustomObjectKeyConstructor(DefaultKeyConstructor):
    retrieve_sql = RetrieveSqlQueryKeyBit()
    updated_at = VideoUpdatedAtKeyBit()
    user = UserKeyBit()


class CustomListKeyConstructor(DefaultKeyConstructor):
    list_sql = ListSqlQueryKeyBit()
    pagination = PaginationKeyBit()
    updated_at = VideoUpdatedAtKeyBit()
    user = UserKeyBit()


logger = logging.getLogger('debug')


class VideoViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    Lists, Creates, Updates, and Retrieves Video Files
    """
    queryset = Video.objects.all().order_by("-created_on")
    serializer_class = VideoSerializer
    action_serializer_classes = {
        "create": CreateVideoSerializer,
        "retrieve": DetailVideoSerializer,
        "update": CreateVideoSerializer
    }
    permission_classes = (CustomDjangoModelPermission, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = VideoFilter
    search_fields = ('title',)
    ordering_fields = ('created_on', 'title', 'duration', 'modified_on')
    parser_classes = (MultiPartParser, FormParser,)

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        print(datetime.now().time())
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(VideoViewSet, self).get_serializer_class()

    @list_route(methods=['get'])
    def get_signed_url(self, request, pk=None):
        key = request.query_params.get("key", None)
        if key:
            signed_url = get_s3_signed_url(key)
            return Response(data={"signed_url": signed_url}, status=status.HTTP_200_OK)

    @cache_response(key_func=CustomObjectKeyConstructor())
    def retrieve(self, *args, **kwargs):
        retrieve_video_response = super(VideoViewSet, self).retrieve(*args, **kwargs)
        retrieve_video_response.data['frame_tags'] = reverse.reverse(viewname='video-frame-tags', kwargs=kwargs,
                                                                     request=self.request)
        retrieve_video_response.data['hard_cuts'] = reverse.reverse(viewname='video-hard-cuts', kwargs=kwargs,
                                                             request=self.request)
        retrieve_video_response.data['trivia'] = reverse.reverse(viewname='video-trivia', kwargs=kwargs,
                                                                 request=self.request)
        retrieve_video_response.data['object_tags'] = reverse.reverse(viewname='video-object-tags', kwargs=kwargs,
                                                                      request=self.request)
        retrieve_video_response.data['compliance_tags'] = reverse.reverse(viewname='video-compliance-tags', kwargs=kwargs,
                                                                          request=self.request)
        retrieve_video_response.data['location_tags'] = reverse.reverse(viewname='video-location-tags', kwargs=kwargs,
                                                                      request=self.request)
        retrieve_video_response.data['foulwords_tags'] = reverse.reverse(viewname='video-foulwords-tags',
                                                                         kwargs=kwargs,
                                                                         request=self.request)
        retrieve_video_response.data['foulwords_tags_en'] = reverse.reverse(viewname='video-foulwords-tags-en',
                                                                            kwargs=kwargs,
                                                                            request=self.request)
        retrieve_video_response.data['face_groups'] = reverse.reverse(
            viewname='video-face-groups', kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['compliance_testing_report'] = reverse.reverse(
            viewname='video-compliance-testing-report', kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['signed_url'] = reverse.reverse(
            viewname='video-signed-url', kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['keyword_tags'] = reverse.reverse(
            viewname='video-keyword-tags', kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['logo_tags'] = reverse.reverse(
            viewname='video-logo-tags', kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['emotions'] = reverse.reverse(
            viewname='video-emotions', kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['ocr_tags'] = reverse.reverse(
            viewname='video-ocr-tags', kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['moderation_tags'] = reverse.reverse(
            viewname='video-moderation-tags', kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['ocr_lang'] = reverse.reverse(
            viewname='video-ocr-lang', kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['credits'] = reverse.reverse(
            viewname='video-credits', kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['auto_video_jobs'] = reverse.reverse(
            viewname='video-auto-video-jobs', kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_metadata'] = reverse.reverse(viewname='video-process-for-metadata',
                                                                               kwargs=kwargs,
                                                                               request=self.request)
        retrieve_video_response.data['latest_process_status'] = reverse.reverse(viewname='video-latest-process-status',
                                                                                kwargs=kwargs,
                                                                                request=self.request)
        retrieve_video_response.data['process_for_tags'] = reverse.reverse(
            viewname='video-process-for-tags',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_objects_aws'] = reverse.reverse(
            viewname='video-process-for-objects-aws',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_emotions_aws'] = reverse.reverse(
            viewname='video-process-for-emotions-aws',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_compliance'] = reverse.reverse(
            viewname='video-process-for-compliance',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_compliance_audio'] = reverse.reverse(
            viewname='video-process-for-compliance-audio',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_nudity'] = reverse.reverse(
            viewname='video-process-for-nudity',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_drugs'] = reverse.reverse(
            viewname='video-process-for-drugs',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_smoking'] = reverse.reverse(
            viewname='video-process-for-smoking',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_alcohol'] = reverse.reverse(
            viewname='video-process-for-drugs',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_sexdolls'] = reverse.reverse(
            viewname='video-process-for-sexdolls',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_fire'] = reverse.reverse(
            viewname='video-process-for-fire',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_flag'] = reverse.reverse(
            viewname='video-process-for-flag',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_statue'] = reverse.reverse(
            viewname='video-process-for-statue',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_location'] = reverse.reverse(
            viewname='video-process-for-location',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_hard_cuts'] = reverse.reverse(
            viewname='video-process-for-hard-cuts',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_face_detect'] = reverse.reverse(
            viewname='video-process-for-face-detect',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_trivia'] = reverse.reverse(
            viewname='video-process-for-trivia',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_keywords'] = reverse.reverse(
            viewname='video-process-for-keywords',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_keywords_hi'] = reverse.reverse(
            viewname='video-process-for-keywords-hi',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_sentiment_en'] = reverse.reverse(
            viewname='video-process-for-sentiment-en',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_sentiment_hi'] = reverse.reverse(
            viewname='video-process-for-sentiment-hi',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_sentiment_mr'] = reverse.reverse(
            viewname='video-process-for-sentiment-mr',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_face_matching'] = reverse.reverse(
            viewname='video-process-for-face-matching',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_logos'] = reverse.reverse(
            viewname='video-process-for-logos',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_samosas'] = reverse.reverse(
            viewname='video-process-for-samosas',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_text_detection'] = reverse.reverse(
            viewname='video-process-for-text-detection',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_rolling_credits'] = reverse.reverse(
            viewname='video-process-for-rolling-credits',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['process_for_emotion'] = reverse.reverse(
            viewname='video-process-for-emotion',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['merge_object_tags'] = reverse.reverse(
            viewname='video-merge-object-tags',
            kwargs=kwargs,
            request=self.request)
        retrieve_video_response.data['get_report'] = reverse.reverse(viewname='video-get-report',
                                                                     kwargs=kwargs,
                                                                     request=self.request)
        retrieve_video_response.data['get_emotions'] = reverse.reverse(viewname='video-get-emotions',
                                                                       kwargs=kwargs,
                                                                       request=self.request)
        retrieve_video_response.data['get_labels'] = reverse.reverse(viewname='video-get-labels',
                                                                     kwargs=kwargs,
                                                                     request=self.request)
        retrieve_video_response.data['get_logos'] = reverse.reverse(viewname='video-get-logos',
                                                                    kwargs=kwargs,
                                                                    request=self.request)
        retrieve_video_response.data['get_foulwords'] = reverse.reverse(viewname='video-get-foulwords',
                                                                        kwargs=kwargs,
                                                                        request=self.request)
        retrieve_video_response.data['send_foulwords'] = reverse.reverse(viewname='video-send-foulwords',
                                                                        kwargs=kwargs,
                                                                        request=self.request)
        retrieve_video_response.data['get_face_groups'] = reverse.reverse(viewname='video-get-face-groups',
                                                                          kwargs=kwargs,
                                                                          request=self.request)
        retrieve_video_response.data['get_face_groups_prm'] = reverse.reverse(viewname='video-get-face-groups-prm',
                                                                              kwargs=kwargs,
                                                                              request=self.request)
        retrieve_video_response.data['get_face_groups_prp'] = reverse.reverse(viewname='video-get-face-groups-prp',
                                                                              kwargs=kwargs,
                                                                              request=self.request)
        retrieve_video_response.data['get_scene_emotions'] = reverse.reverse(viewname='video-get-scene-emotions',
                                                                             kwargs=kwargs,
                                                                             request=self.request)
        retrieve_video_response.data['get_cognitive_report'] = reverse.reverse(viewname='video-get-cognitive-report',
                                                                              kwargs=kwargs,
                                                                              request=self.request)

        return retrieve_video_response

    @cache_response(key_func=CustomListKeyConstructor())
    def list(self, *args, **kwargs):
        return super(VideoViewSet, self).list(*args, **kwargs)

    @detail_route(methods=['get'])
    def process_for_objects_aws(self, request, pk =None):

        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Objects AWS')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)

        return Response({"process id":str(auto.id)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_emotions_aws(self, request, pk =None):

        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Emotion AWS')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)

        return Response({"process id":str(auto.id)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_face_detect(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Faces')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_emotion(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Emotion')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def frame_tags(self, request, pk=None):
        video = self.get_object()
        frame_tags_serializer = FrameTagSerializer(video.frametag.all().order_by('frame_in'), context={"request": request}, many=True)
        return Response(frame_tags_serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def hard_cuts(self, request, pk=None):
        video = self.get_object()
        video_id = str(video.id)
        hard_cuts_serializer = HardCutsSerializer(video.hardcuts, context={"request": request})
        return Response(hard_cuts_serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def manual_tags(self, request, pk=None):
         video = self.get_object()
         video_id = str(video.id)
         manual_tags_serializer = ManualTagSerializer(video.manualtag.all().order_by('frame_in'), context={"request": request}, many=True)
         return Response(manual_tags_serializer.data, status=status.HTTP_200_OK)


    @detail_route(methods=['get'])
    def merge_object_tags(self, request, pk=None):
        video = self.get_object()
        merge_object_detections.delay(True, video.id)
        return Response(data={"status": "started"}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def object_tags(self,request, pk=None):

        video = self.get_object()
        name_search = request.query_params.get("name", "")

        with open("./utils/moderation.txt", 'r') as fd:
            filter_list = [f.strip() for f in fd.readlines()]
        query = reduce(operator.or_, (Q(tag__title__icontains=item)for item in filter_list))

        if name_search:
            tags = video.frametag.filter(tag__parent__title__iexact="Others", tag__title__icontains=name_search).exclude(query).values("tag__title").distinct()
            tags_manual = video.manualtag.filter(tags__title__isnull=False, tags__title__icontains=name_search).values("tags__title", "tags__parent__title").distinct()
        else:
            tags = video.frametag.filter(tag__parent__title__iexact="Others").exclude(query).values("tag__title").distinct()
            tags_manual = video.manualtag.filter(tags__title__isnull=False).values("tags__title", "tags__parent__title").distinct()
        data = []

        for tag in tags:
            name = tag['tag__title']
            object_url = get_display_images_link(name)
            frametags = video.frametag.all().order_by('frame_in').filter(tag__title__iexact=name, tag__parent__title__iexact="Others")
            obj = {}
            obj['name'] = name
            obj['poster'] = object_url if object_url else ""
            obj['timeline'] = []
            obj['id'] = uuid.uuid4()
            obj['type'] = "object"
            obj['tag_type'] = "automatic"

            dur = 0
            for lt in frametags:
                obj['timeline'].append(
                    {
                        "startTime": str(format(lt.frame_in/lt.video.frame_rate, '.2f')),
                        "endTime": str(format(lt.frame_out/lt.video.frame_rate, '.2f'))
                    }
                )
                dur += (lt.frame_out-lt.frame_in)/lt.video.frame_rate
            obj['duration'] = format(dur, '.2f')
            data.append(obj)

        for tag in tags_manual:
            # print("tag")
            name = tag['tags__title']
            parent = tag['tags__parent__title']
            manual_tags = video.manualtag.all().order_by('frame_in').filter(tags__title__iexact=name, tags__parent__title__iexact=parent)
            obj = {}
            color_list = ["Red", "Yellow", "Green", "Blue", "Black", "White", "Orange", "Violet", "Pink", "Brown", "Grey", "None"]
            x = list(filter(lambda x: name == x, color_list))
            logging.info(x)

            if len(x) >= 1:
                obj['name'] = name + " " + parent
            else:
                obj['name'] = name
            object_url = get_display_images_link(name)
            logging.info(obj['name'])
            obj['poster'] = object_url if object_url else ""
            obj['timeline'] = []
            obj['id'] = uuid.uuid4()
            obj['type'] = "object"
            obj['tag_type'] = "manual"

            dur = 0
            for lt in manual_tags:
                obj['timeline'].append(
                    {
                        "startTime": str(format(lt.frame_in/lt.video.frame_rate, '.2f')),
                        "endTime": str(format(lt.frame_out/lt.video.frame_rate, '.2f'))
                    }
                )
                dur += (lt.frame_out-lt.frame_in)/lt.video.frame_rate
            obj['duration'] = format(dur, '.2f')
            data.append(obj)

        data.sort(key=lambda x: -1 * float(x['duration']))

        # with open("./utils/moderation.txt", 'r') as fd:
        #     filter_list = [f.strip() for f in fd.readlines()]
        #
        # query = reduce(operator.or_, (Q(tag__name__icontains=item) for item in filter_list))
        # object_tags_serializer = FrameTagSerializer(video.frametag.all().filter(query).
        #                                             order_by('frame_in'), context={"request": request}, many=True)

        return Response(data, status=status.HTTP_200_OK)

    # @detail_route(methods=['get'])
    # def compliance_testing_report(self, request, pk=None):
    #     video_instance = self.get_object()
    #     video_id = str(video_instance.id)
    #     frametags = video_instance.checktag.filter(autotag__parent__title__in=["Compliance" ,"Programming", "Drugs", "Alcohol", "Fire", "Sex Dolls", "Indian Flag", "Naked Statue", "Nudity"]).order_by("frame_in")
    #     report = []
    #     for frametag in frametags:
    #         if frametag.usertag:
    #             report.append([frametag._time_in(), frametag._time_out(), frametag.autotag.title, frametag.usertag.title])
    #     report_df = pd.DataFrame(report, columns=["Start Time", "End Time", "Predicted", "Actual"])
    #     y_pred = list(report_df["Predicted"]) 
    #     y_actual = list(report_df["Actual"])
    #     y_actual = ['None' if v is None else v for v in y_actual]
    #     y_pred = ['None' if v is None else v for v in y_pred]
    #     accuracy_report = classification_report(y_actual, y_pred, output_dict=True)
    #     accuracy_df = pd.DataFrame(accuracy_report).transpose()
    #     file_name = '/tmp/{}.xlsx'.format(video_id)
    #     zip_file_name = '/tmp/{}.zip'.format(video_id)
    #     writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
    #     report_df.to_excel(writer, sheet_name="Report")
    #     accuracy_df.to_excel(writer, sheet_name="Accuracy")
    #     writer.save()
    #     zipObj = zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED)
    #     zipObj.write(file_name, "AccuracyReport.xlsx")
    #     zipObj.close()
    #     os.remove(file_name)
    #     response = HttpResponse(open(zip_file_name, 'rb').read())
    #     os.remove(zip_file_name)
    #     return response

    @detail_route(methods=['get'])
    def compliance_testing_report(self, request, pk=None):
        video_instance = self.get_object()
        video_id = str(video_instance.id)
        frametags = video_instance.frametag.filter(tag__parent__title__in=["Compliance" ,"Programming", "Drugs", "Alcohol", "Fire", "Sex Dolls", "Indian Flag", "Naked Statue", "Nudity"]).order_by("frame_in")
        report = []
        for frametag in frametags:
            if frametag.tag.title == "Testing":
                report.append([frametag._time_in(), frametag._time_out(), "Incorrect", frametag.words])
            else:
                report.append([frametag._time_in(), frametag._time_out(), frametag.words, frametag.comment])
        report_df = pd.DataFrame(report, columns=["Start Time", "End Time", "Predicted", "Actual"])
        y_pred = list(report_df["Predicted"]) 
        y_actual = list(report_df["Actual"])
        y_actual = ['None' if v is None else v for v in y_actual]
        y_pred = ['None' if v is None else v for v in y_pred]
        accuracy_report = classification_report(y_actual, y_pred, output_dict=True)
        accuracy_df = pd.DataFrame(accuracy_report).transpose()
        file_name = '/tmp/{}.xlsx'.format(video_id)
        zip_file_name = '/tmp/{}.zip'.format(video_id)
        writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
        report_df.to_excel(writer, sheet_name="Report")
        accuracy_df.to_excel(writer, sheet_name="Accuracy")
        writer.save()
        zipObj = zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED)
        zipObj.write(file_name, "AccuracyReport.xlsx")
        zipObj.close()
        os.remove(file_name)
        response = HttpResponse(open(zip_file_name, 'rb').read())
        os.remove(zip_file_name)
        return response


    @detail_route(methods=['get'])
    def location_tags(self,request, pk=None):
        video = self.get_object()
        tags = video.manualtag.filter(tags__parent__title="Location").values("tags__title").distinct()
        data = []
        for tag in tags:
            name = tag['tags__title']
            frametags = video.manualtag.all().order_by('frame_in').filter(tags__title=name, tags__parent__title="Location")
            location_url = get_display_images_link(name)
            obj = {}
            obj['name'] = name
            obj['poster'] = location_url if location_url else ""
            obj['timeline'] = []
            obj['id'] = uuid.uuid4()
            obj['type'] = "location"

            dur = 0
            for lt in frametags:
                obj['timeline'].append(
                    {
                        "startTime": str(format(lt.frame_in/lt.video.frame_rate, '.2f')),
                        "endTime": str(format(lt.frame_out/lt.video.frame_rate, '.2f'))
                    }
                )
                dur += (lt.frame_out-lt.frame_in)/lt.video.frame_rate
            obj['duration'] = format(dur, '.2f')
            data.append(obj)
        data.sort(key=lambda x: -1 * float(x['duration']))

        return Response(data, status=status.HTTP_200_OK)
    
  
    @detail_route(methods=['get'])
    def logo_tags(self,request, pk=None):
        video = self.get_object()
        tags = video.frametag.filter(tag__parent__title__iexact="Logo").values("tag__title").distinct()
        data = []
        for tag in tags:
            name = tag['tag__title'].upper()
            frametags = video.frametag.all().order_by('frame_in').filter(tag__title__iexact=name, tag__parent__title__iexact="Logo")
            logo_url = get_display_images_link(name)
            obj = {}
            obj['name'] = name
            obj['poster'] = logo_url if logo_url else ""
            obj['timeline'] = []
            obj['id'] = uuid.uuid4()
            obj['type'] = "Logo"

            dur = 0
            for lt in frametags:
                obj['timeline'].append(
                    {
                        "startTime": str(format(lt.frame_in/lt.video.frame_rate, '.2f')),
                        "endTime": str(format(lt.frame_out/lt.video.frame_rate, '.2f'))
                    }
                )
                dur += (lt.frame_out-lt.frame_in)/lt.video.frame_rate
            obj['duration'] = format(dur, '.2f')
            data.append(obj)
        data.sort(key=lambda x: -1 * float(x['duration']))

        return Response(data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def compliance_tags(self,request, pk=None):
        video = self.get_object()

        compliance_tags_serializer = FrameTagSerializer(video.frametag.all().filter(tag__category__name="Compliance").
                                                        order_by("frame_in"), context={"request": request}, many=True)
        return Response(compliance_tags_serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def signed_url(self,request, pk=None):
        video_url = self.get_object().file
        video_name = self.get_object().title
        signed_url = s3_signed_url(video_url, video_name)
        return Response(data={"signed_url": signed_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def moderation_tags(self, request, pk=None):
        
        word_search = request.query_params.get("name", "")
        
        video = self.get_object()
        with open("./utils/moderation.txt", 'r') as fd:
            filter_list = [f.strip() for f in fd.readlines()]
        query = reduce(operator.or_, (Q(tag__title__icontains=item.strip())&Q(collection=None)&Q(index=None) for item in filter_list))

        if word_search:
            compliance_tags_serializer = FrameTagSerializer(video.frametag.filter(tag__parent__title__in=compliance_tags, words__icontains=word_search).order_by("frame_in"), context={"request": request}, many=True)
            keyword_serializer = KeywordTagSerializer(video.keywords.all().filter(tags__name="Profanity", words__icontains=word_search).order_by('frame_in'),
                                                  context={"request": request}, many=True)
        else: 
            compliance_tags_serializer = FrameTagSerializer(video.frametag.filter(tag__parent__title__in=compliance_tags).order_by("frame_in"), context={"request": request}, many=True)
            keyword_serializer = KeywordTagSerializer(video.keywords.all().filter(tags__name="Profanity").order_by('frame_in'),
                                                  context={"request": request}, many=True)
        index = 0
        for keyword in keyword_serializer.data:
            words = keyword['words']
            words = "<b>{}</b>".format(words)
            keyword_serializer.data[index]['words'] = words
            keyword_serializer.data[index]['tagname'] = 'profanity'
            keyword_serializer.data[index]['category'] = 'Compliance'
            index += 1
        final_data = compliance_tags_serializer.data
        index = 0
        for f in final_data:
            if any([ r in f['tagname'] for r in ['smoke', 'smoking', 'fire', 'flame', 'ciggarette']]):
                final_data[index]['category'] = 'smoking'
            if any([ r in f['tagname'] for r in ['beer', 'drinking', 'party', 'soft drinking', 'liquor store', 'wine', 'cola', 'champagne', 'carbonated soft drinks', 'drink', 'liqueur', 'alcohol' ]]):
                final_data[index]['category'] = 'drinking'
            if any([ r in f['tagname'] for r in ['skin', 'chest', 'thigh', 'racy', 'adult', 'leg', 'body', 'kiss', 'nudity']]):
                final_data[index]['category'] = 'nudity'
            if any([ r in f['tagname'] for r in ['demolition', 'violence', 'weapon', 'fire arm', 'fire', 'flame', 'aggression', 'explosive', 'gun', 'gunshot', 'shooting', 'arrest']]):
                final_data[index]['category'] = 'violence'
            index +=1
        final_data += keyword_serializer.data
        final_data = sorted(final_data, key=itemgetter('frame_in'))
        return Response(data=final_data, status=status.HTTP_200_OK)


    @detail_route(methods=['get'])
    def single_moderation_tags(self, request, pk=None):

        video = self.get_object()

        compliance_tags_serializer = FrameTagSerializer(video.frametag.filter(tag__parent__title__iexact="Compliance").order_by("frame_in"), context={"request": request}, many=True)

        keyword_serializer = KeywordTagSerializer(video.keywords.all().order_by('frame_in'),
                                                  context={"request": request}, many=True)
        index = 0
        for keyword in keyword_serializer.data:
            words = keyword['words']
            words = "<b>{}</b>".format(words)
            keyword_serializer.data[index]['words'] = words
            keyword_serializer.data[index]['tagname'] = 'profanity'
            keyword_serializer.data[index]['category'] = 'Compliance'
            index += 1

        final_data = compliance_tags_serializer.data
        index = 0
        for f in final_data:
            if any([r in f['tagname'] for r in ['smoke', 'smoking', 'fire', 'flame']]):
                final_data[index]['category'] = 'smoking'
            if any([r in f['tagname'] for r in
                    ['beer', 'drinking', 'party', 'soft drinking', 'liquor store', 'wine', 'cola', 'champagne',
                     'carbonated soft drinks', 'drink', 'liqueur', 'alcohol']]):
                final_data[index]['category'] = 'drinking'
            if any([r in f['tagname'] for r in ['skin', 'chest', 'thigh', 'racy', 'adult', 'leg', 'body', 'kiss']]):
                final_data[index]['category'] = 'nudity'
            if any([r in f['tagname'] for r in
                    ['demolition', 'violence', 'weapon', 'fire arm', 'fire', 'flame', 'aggression', 'explosive', 'gun',
                     'gunshot', 'shooting', 'arrest']]):
                final_data[index]['category'] = 'violence'
            index += 1
        final_data += keyword_serializer.data
        final_data = sorted(final_data, key=itemgetter('frame_in'))
        return Response(data=final_data, status=status.HTTP_200_OK)


    @detail_route(methods=['get'])
    def trivia(self, request, pk=None):
        video_obj = self.get_object()
        face_groups = FaceGroup.objects.all().filter(video=video_obj)
        persons = []

        for face_group in face_groups:
            try:
                print(face_group.person.name)
                persons.append(face_group.person.name)
            except AttributeError:
                print("None")
                pass

        # load the trivia

        with open('./content/trivia.json', 'r+') as f:
            trivia = {}
            trivia['persons'] = persons
            trivia['trivia'] = {}
            trivia_obj = json.load(f)
            for person in persons:
                try:
                    new_trivia = list(map(lambda x: person +" : "+x, trivia_obj[person]))
                    random.shuffle(new_trivia)
                    trivia['trivia'][person] = new_trivia[0:5]
                    # trivia = list(itertools.chain(trivia['trivia'], new_trivia[0:5]))
                except KeyError or TypeError:
                    pass

            return Response(data={"trivia": trivia}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def keyword_tags(self, request, pk=None):
        video = self.get_object()
        is_filtered = is_blacklisted(request)

        if is_filtered:
            last_published_date = get_latest_publication()
            keyword_serializer = KeywordTagSerializer(video.keywords.filter(created_on__lte=last_published_date).order_by('frame_in'), context={"request": request}, many=True)
        else:
            keyword_serializer = KeywordTagSerializer(video.keywords.all().order_by('frame_in'), context={"request": request}, many=True)

        return Response(keyword_serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def ocr_tags(self, request, pk=None):
        video = self.get_object()
        ocr_tags = video.ocrtags.all().order_by('frame_in')
        ocr_serializer = OCRTagSerializer(ocr_tags, context={"request": request}, many=True)
        return Response(ocr_serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def ocr_lang(self, request, pk=None):
        video = self.get_object()
        ocr_tags = video.ocrtags.all().order_by('frame_in')
        ocr_serializer = OCRTagSerializer(ocr_tags, context={"request": request}, many=True)
        languages = ocr_tags.values('language').distinct()
        languages = [l['language'] for l in languages]
        seg_data = {}
        for l in languages:
            seg_data[l] = []
        for keyword in ocr_serializer.data:
            lang = keyword['language']
            if keyword['words'] !='-':
                seg_data[lang].append(keyword)
        return Response(seg_data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def foulwords_tags(self, request, pk=None):
        video = self.get_object()
        with codecs.open("./utils/foul.txt", 'r', encoding='utf-8') as fd:
            filter_list = [f.strip() for f in fd.readlines()]
        # print(filter_list)
        query = reduce(operator.or_, (Q(words__icontains=item) for item in filter_list))
        keyword_serializer = KeywordTagSerializer(video.keywords.all().filter(query).order_by('frame_in'),
                                                  context={"request": request}, many=True)
        index = 0
        filter_q = '|'.join(filter_list)
        for keyword in keyword_serializer.data:
            words = keyword['words']

            words = re.sub(r'({})'.format(filter_q), r'<b>\1</b>', words, flags=re.I)
            keyword_serializer.data[index]['words'] = words
            index += 1
        return Response(keyword_serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def foulwords_tags_en(self, request, pk=None):
        video = self.get_object()
        with codecs.open("./utils/foul.txt", 'r', encoding='utf-8') as fd:
            filter_list = [f.strip() for f in fd.readlines()]
        # print(filter_list)
        query = reduce(operator.or_, (Q(words__icontains=item) for item in filter_list))
        keyword_serializer = KeywordTagSerializer(video.keywords.all().filter(query).order_by('frame_in'),
                                                  context={"request": request}, many=True)
        index = 0
        filter_q = '|'.join(filter_list)
        for keyword in keyword_serializer.data:
            words = keyword['words']
            words = transliterate(words, sanscript.DEVANAGARI, sanscript.HK)
            keyword_serializer.data[index]['words'] = words.lower()
            index += 1
        return Response(keyword_serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def face_groups(self, request, pk=None):
        video = self.get_object()
        name_search = request.query_params.get("name", "")
        if name_search:
            face_group_serializer = FaceGroupSerializer(FaceGroup.objects.filter(video=video, person__name__icontains=name_search).order_by("person"), context={"request": request}, many=True)
            fg = FaceGroup.objects.filter(Q(video=video) & Q(person__name__icontains=name_search)).values("person__name").distinct()
        else:
            face_group_serializer = FaceGroupSerializer(FaceGroup.objects.all().filter(video=video, person__isnull=True).order_by("person"), context={"request": request}, many=True)
            fg = FaceGroup.objects.all().filter(Q(video=video) & Q(person__isnull=False)).values("person__name").distinct()
        f_data = []
        for p in fg:
            final_timeline = [0] * int(math.ceil(video.duration))
            person_name = p['person__name']
            facegroup_id = str(FaceGroup.objects.filter(video=video, person__name__iexact=person_name).first().id)
            fgs = FaceGroup.objects.all().filter(Q(video=video) & Q(person__name=person_name))
            p_first = fgs.first()
            p_ser = FaceGroupSerializer(p_first, context={"request": request})
            p_data = p_ser.data


            for f in fgs:
                timeline = f.timeline
                for ind in range(int(len(timeline) / 2)):
                    t1 = timeline[ind * 2]
                    t2 = timeline[ind * 2 + 1]
                    final_timeline[t1: t2 + 1] = [1] * (t2 + 1 - t1)
            print_timeline = []
            index = 0
            duration = 0
            for f in final_timeline:
                if f == 1:
                    duration += 1
                    if print_timeline:
                        # check for continuity
                        if print_timeline[-1][1] == index - 1 or print_timeline[-1][1] == index:
                            print_timeline[-1][1] = index
                        elif print_timeline[-1][1] < index:
                            print_timeline.append([index, index + 1])
                    else:
                        print_timeline.append([index, index + 1])
                index += 1
            percent = duration * 100 / video.duration
            list_timeline = []
            for p_time in print_timeline:
                list_timeline.append(
                    {
                        "startTime": p_time[0],
                        "endTime": p_time[1]
                    }
                )
            base_url = request.build_absolute_uri().split("videos/")[0]
            extended_url = "facegroups/{}/".format(facegroup_id)
            extended_url = base_url + extended_url
            face_url = get_display_images_link(person_name)
            face_img = face_url if face_url else p_data['poster']
            data = {
                "id" : facegroup_id,
                "url": extended_url,
                "face_image":face_img,
                "person":p_data['person'],
                "character":"",
                "modified_timeline":list_timeline,
                "timeline":list_timeline,
                "poster":face_img,
                "timeline_length":"",
                "duration":duration,
                "name":p_data['name'],
                "type": "facegroup"
            }
            f_data.append(data)
        f_data += face_group_serializer.data
        f_data.sort(key=lambda x: -1 * x["duration"])
        return Response(f_data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def get_face_groups(self, request, pk=None):
        video = self.get_object()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Report.csv"'
        writer = csv.writer(response)
        fg = FaceGroup.objects.all().filter(Q(video=video)&Q(person__isnull=False)).order_by("person")
        for i in range(int(math.ceil(video.duration))):
            row_data = [i]
            for f in fg:
                timeline = f.timeline
                for ind in range(int(len(timeline) / 2)):
                    t1 = timeline[ind * 2]
                    t2 = timeline[ind * 2 + 1]
                    if t1 <= i <= t2:
                        row_data.append(f.person.name)
                        break
            writer.writerow(row_data)
        return response

    @detail_route(methods=['get'])
    def get_face_groups_prm(self, request, pk=None):
        video = self.get_object()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Report.csv"'
        writer = csv.writer(response)
        fg = FaceGroup.objects.all().filter(Q(video=video) & Q(person__isnull=False)).order_by("person")
        for i in range(int(math.ceil(video.duration))):
            row_data = [i]
            for f in fg:
                timeline = f.timeline
                for ind in range(int(len(timeline) / 2)):
                    t1 = timeline[ind * 2]
                    t2 = timeline[ind * 2 + 1]
                    if t1 <= i <= t2:
                        row_data.append(f.person.name)
                        one_face = Face.objects.filter(face_group=f)[0]
                        prm = math.ceil(((one_face.face_rect.w*one_face.face_rect.h)/(video.height*video.width))*100)
                        row_data.append(prm)
                        break
            writer.writerow(row_data)
        return response

    @detail_route(methods=['get'])
    def get_keywords(self, request, pk=None):
        video = self.get_object()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Report.csv"'
        writer = csv.writer(response)
        kt = video.keywords.all().order_by('frame_in')
        for i in range(len(kt)):
            tag = kt[i]
            time_in = (str(timedelta(seconds=math.floor(tag.frame_in / tag.video.frame_rate))) + ":" + (str(
                tag.frame_in - math.floor(
                    tag.video.frame_rate * math.floor(tag.frame_in / tag.video.frame_rate)))).zfill(2)).zfill(11)
            time_out = (str(timedelta(seconds=math.floor(tag.frame_out / tag.video.frame_rate))) + ":" + (str(
                tag.frame_out - math.floor(
                    tag.video.frame_rate * math.floor(tag.frame_out / tag.video.frame_rate)))).zfill(2)).zfill(11)
            writer.writerow([time_in, time_out, tag.words])
        return response

    @detail_route(methods=['get'])
    def get_face_groups_prp(self, request, pk=None):
        video = self.get_object()
        fps = video.frame_rate
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Report.csv"'
        writer = csv.writer(response)
        fg = FaceGroup.objects.all().filter(Q(video=video) & Q(person__isnull=False)).values("person__name").distinct()
        for p in fg:
            final_timeline = [0] * int(math.ceil(video.duration))
            person_name = p['person__name']
            fgs = FaceGroup.objects.all().filter(Q(video=video) & Q(person__name=person_name))
            for f in fgs:
                timeline = f.timeline
                for ind in range(int(len(timeline) / 2)):
                    t1 = timeline[ind * 2]
                    t2 = timeline[ind * 2 + 1]
                    final_timeline[t1: t2+1] =[1]*(t2+1-t1)
            print_timeline = []
            index = 0
            duration = 0
            for f in final_timeline:
                if f==1:
                    duration += 1
                    if print_timeline:
                        # check for continuity
                        if print_timeline[-1][1]==index-1 or print_timeline[-1][1]==index:
                            print_timeline[-1][1]=index
                        elif print_timeline[-1][1]<index:
                            print_timeline.append([index, index+1])
                    else:
                        print_timeline.append([index, index+1])
                index+=1
            percent = duration*100/video.duration
            writer.writerow([person_name, "", "", "duration", duration, 'percent', "{0:.2f}".format(percent)])
            for t in print_timeline:
                writer.writerow(["", sec2TCR(t[0], fps), sec2TCR(t[1], fps)])

        return response

    @detail_route(methods=['get'])
    def credits(self, request, pk=None):
        video = self.get_object()
        try:
            credit_obj = Credit.objects.get(video=video)
        except ObjectDoesNotExist:
            credit_obj = None
            pass
        credit_data = {}
        if credit_obj:
            credit_data = credit_obj.credit
        return Response(data={"credits": credit_data}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def auto_video_jobs(self, request, pk=None):
        video = self.get_object()
        auto_video_job_serializer = AutoVideoJobSerializer(
            AutoVideoJob.objects.all().filter(video=video),
            context={"request": request}, many=True)
        return Response(auto_video_job_serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def latest_process_status(self, request, pk=None):
        video = self.get_object()
        auto_video_job_serializer = AutoVideoJobSerializer(
            AutoVideoJob.objects.all().filter(video=video).order_by("job_type", "-created_on").distinct("job_type"),
            context={"request": request}, many=True)
        return Response(auto_video_job_serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_metadata(self, request, pk=None):
        video_instance = self.get_object()
        video_serializer = CreateVideoSerializer(video_instance, partial=True)
        video_file = video_serializer.data['file']
        set_metadata.delay(video_file, video_serializer.data['id'])
        return Response(video_serializer.data,status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def get_report(self, request, pk=None):
        video_instance = self.get_object()

        # Create the HttpResponse object with the appropriate PDF headers.
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Report.pdf"'

        buffer = BytesIO()

        report = PrintFrameTags(buffer, 'Letter')
        pdf = report.print_frame_tags(pk, user= self.request.user, request=request)

        response.write(pdf)
        return response

    @detail_route(methods=['get'])
    def get_labels(self, request, pk=None):
        video_instance = self.get_object()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Report.csv"'
        writer = csv.writer(response)
        labelsToFilter = ["xylophone", "vision"]
        for tag in video_instance.frametag.all().filter(tag__category__name="Others").order_by('frame_in'):
            if not any(label in tag.tag.name for label in labelsToFilter):
                time_in = (str(timedelta(seconds=math.floor(tag.frame_in/tag.video.frame_rate)))+":"+(str(tag.frame_in - math.floor(tag.video.frame_rate*math.floor(tag.frame_in/tag.video.frame_rate)))).zfill(2)).zfill(11)
                time_out = (str(timedelta(seconds=math.floor(tag.frame_out/tag.video.frame_rate)))+":"+(str(tag.frame_out - math.floor(tag.video.frame_rate*math.floor(tag.frame_out/tag.video.frame_rate)))).zfill(2)).zfill(11)
                writer.writerow([time_in, time_out, tag.tag.name])
        return response

    @detail_route(methods=['get'])
    def emotions(self,request, pk=None):
        video = self.get_object()
        frame_rate = video.frame_rate
        tags = video.emotiontag_set.all().values("emotion_quo").distinct()
        if tags:
            data = []
            for tag in tags:
                name = tag['emotion_quo']
                emotiontags = video.emotiontag_set.all().order_by('frame_in').filter(emotion_quo=name).values("frame_in", "frame_out").distinct()
                obj = {}
                obj['name'] = name
                obj['timeline'] = []
                obj['id'] = str(uuid.uuid4())

                dur = 0
                for lt in emotiontags:
                    obj['timeline'].append(
                        {
                            "startTime": str(format(lt['frame_in']/frame_rate, '.2f')),
                            "endTime": str(format(lt['frame_out']/frame_rate, '.2f'))
                        }
                    )
                    dur += (lt['frame_out']-lt['frame_in'])/frame_rate
                obj['duration'] = format(dur, '.2f')
                obj['percent'] = "{0:.2f}".format(dur*100/video.duration)
                data.append(obj)
            data.sort(key=lambda x: -1 * float(x['duration']))

            return Response(data, status=status.HTTP_200_OK)

        else:
            video_instance = video
            faces = Face.objects.filter(face_group__video=video_instance)
            time_line_not_sorted = {}
            time_line_filtered = {}

            for face in faces:
                video_frame = VideoFrame.objects.get(frame=face.face_rect.frame)
                try:
                    time_line_not_sorted[face.emotion].append(int(video_frame.time))
                except KeyError:
                    time_line_not_sorted[face.emotion] = [int(video_frame.time)]

            for td in time_line_not_sorted:
                time_line_filtered[td] = []
                for t in sorted(time_line_not_sorted[td]):
                    if not time_line_filtered[td]:
                        time_line_filtered[td].append(t)
                        time_line_filtered[td].append(t + 1)
                    elif t - 2 <= time_line_filtered[td][-1] <= t:
                        time_line_filtered[td][-1] = t
                    elif time_line_filtered[td][-1] > t:
                        continue
                    else:
                        time_line_filtered[td].append(t)
                        time_line_filtered[td].append(t + 1)
            output = []
            for td in time_line_filtered:
                timeline = time_line_filtered[td]
                modified_timeline = []
                dur = 0
                
                for i in range(int(len(timeline) / 2)):
                    modified_timeline.append({"startTime": timeline[i * 2], "endTime": timeline[i * 2 + 1] + 1})
                    dur += timeline[i * 2 + 1] - timeline[i * 2]
                if td == "sadness":
                    td="sad"
                elif td == "happiness":
                    td='happy'
                object_url = get_display_images_link(td)

                output.append(
                    {

                        'id': uuid.uuid4(),
                        'name': td,
                        'timeline': modified_timeline,
                        'duration': dur,
                        'percent': "{0:.2f}".format(dur*100/video_instance.duration),
                        'poster': object_url if object_url else ""
                    }
                )

            return Response(data=output, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def get_scene_emotions(self, request, pk=None):
        video = self.get_object()
        data = []
        tags = video.emotiontag_set.all().values("emotion_quo").distinct()
        for tag in tags:
            name = tag['emotion_quo']
            emotion_tags = video.emotiontag_set.all().order_by('frame_in').filter(emotion_quo=name)
            for lt in emotion_tags:
                obj={
                    "startTime": str(format(lt.frame_in / lt.video.frame_rate, '.2f')),
                    "endTime": str(format(lt.frame_out / lt.video.frame_rate, '.2f')),
                    "name": name,
                    "id" : uuid.uuid4(),
                    }
                data.append(obj)
        return Response(data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def get_emotions(self, request, pk=None):
        video_instance = self.get_object()
        fps = video_instance.frame_rate
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Report.csv"'
        writer = csv.writer(response)
        faces = Face.objects.filter(face_group__video=video_instance)
        time_line_not_sorted = {}
        time_line_filtered = {}

        for face in faces:
            video_frame = VideoFrame.objects.get(frame=face.face_rect.frame)
            try:
                time_line_not_sorted[face.emotion].append(int(video_frame.time))
            except KeyError:
                time_line_not_sorted[face.emotion] = [int(video_frame.time)]

        for td in time_line_not_sorted:
            time_line_filtered[td] = []
            for t in sorted(time_line_not_sorted[td]):
                if not time_line_filtered[td]:
                    time_line_filtered[td].append(t)
                    time_line_filtered[td].append(t + 1)
                elif t - 2 <= time_line_filtered[td][-1] <= t:
                    time_line_filtered[td][-1] = t
                elif time_line_filtered[td][-1] > t:
                    continue
                else:
                    time_line_filtered[td].append(t)
                    time_line_filtered[td].append(t + 1)

        for td in time_line_filtered:
            duration = 0
            if td == 'sadness':
                row_data = ['sad', "", ""]
            elif td == 'happiness':
                row_data = ['happy', "", ""]
            else :
                row_data = [td, "", ""]
            writer_row_data = []
            writer_row_data.append(row_data)
            timeline = time_line_filtered[td]

            for i in range(int(len(timeline) / 2)):
                row_data = ["", sec2TCR(timeline[i * 2], fps), sec2TCR(timeline[i * 2 + 1], fps)]
                duration += timeline[i * 2 + 1] - timeline[i * 2]
                writer_row_data.append(row_data)
            percent = duration*100/video_instance.duration
            writer_row_data[0] += ['duration', duration, 'percent', "{0:.2f}".format(percent)]
            for r in writer_row_data:
                writer.writerow(r)
        return response

    @detail_route(methods=['get'])
    def get_logos(self, request, pk=None):
        video = self.get_object()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Report.csv"'
        writer = csv.writer(response)
        tags = video.logotag.all().filter(~Q(tag__name="cpplus"))
        for tag in tags:
            time_in = (str(timedelta(seconds=math.floor(tag.frame_in / tag.video.frame_rate))) + ":" + (str(
                tag.frame_in - math.floor(
                    tag.video.frame_rate * math.floor(tag.frame_in / tag.video.frame_rate)))).zfill(2)).zfill(11)
            time_out = (str(timedelta(seconds=math.floor(tag.frame_out / tag.video.frame_rate))) + ":" + (str(
                tag.frame_out - math.floor(
                    tag.video.frame_rate * math.floor(tag.frame_out / tag.video.frame_rate)))).zfill(2)).zfill(11)
            writer.writerow([time_in, time_out, tag.tag.name])
        return response

    @detail_route(methods=['get'])
    def get_foulwords(self, request, pk=None):
        video = self.get_object()
        compliance_tags_serializer = FrameTagSerializer(video.frametag.all().filter(tag__category__name="Compliance").
                                                        order_by("frame_in"), context={"request": request}, many=True)

        with codecs.open("./utils/foul.txt", 'r', encoding='utf-8') as fd:
            filter_list = [f.strip() for f in fd.readlines()]
            tmp_list = []
            for f in filter_list:
                tmp_list.append(" {}".format(f))
                tmp_list.append("{} ".format(f))
                tmp_list.append("{},".format(f))
                tmp_list.append("{}.".format(f))
        query = reduce(operator.or_, (Q(words__icontains=item) for item in tmp_list))
        keyword_serializer = KeywordTagSerializer(video.keywords.all().filter(query&(Q(is_approved='ACP')|Q(is_approved='CHK')|Q(is_approved='CLN'))).order_by('frame_in'),
                                                  context={"request": request}, many=True)
        index = 0
        for keyword in keyword_serializer.data:
            words = keyword['words']
            keyword_serializer.data[index]['words'] = words
            keyword_serializer.data[index]['tagname'] = 'profanity'
            keyword_serializer.data[index]['category'] = 'Compliance'
            index += 1
        final_data = compliance_tags_serializer.data
        final_data += keyword_serializer.data
        final_data = sorted(final_data, key=itemgetter('frame_in'))

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Report.csv"'
        writer = csv.writer(response)

        for tag in final_data:
            time_in = (str(timedelta(seconds=math.floor(tag['frame_in'] / video.frame_rate))) + ":" + (str(
                tag['frame_in'] - math.floor(
                    video.frame_rate * math.floor(tag['frame_in'] / video.frame_rate)))).zfill(2)).zfill(11)
            time_out = (str(timedelta(seconds=math.floor(tag['frame_out'] / video.frame_rate))) + ":" + (str(
                tag['frame_out'] - math.floor(
                    video.frame_rate * math.floor(tag['frame_out'] / video.frame_rate)))).zfill(2)).zfill(11)

            writer.writerow([time_in, time_out, tag['words']])

        return response

    @detail_route(methods=['get'])
    def send_foulwords(self, request, pk=None):
        emails = request.query_params.get("emails", "aswin@tessact.com")
        groups = request.query_params.get("groups", "bc050b80-ee62-4b26-9b4d-7533bb92b953")

        video = self.get_object()
        compliance_tags_serializer = FrameTagSerializer(video.frametag.all().filter(tag__category__name="Compliance").
                                                        order_by("frame_in"), context={"request": request}, many=True)

        with codecs.open("./utils/foul.txt", 'r', encoding='utf-8') as fd:
            filter_list = [f.strip() for f in fd.readlines()]
            tmp_list = []
            for f in filter_list:
                tmp_list.append(" {}".format(f))
                tmp_list.append("{} ".format(f))
                tmp_list.append("{},".format(f))
                tmp_list.append("{}.".format(f))
        query = reduce(operator.or_, (Q(words__icontains=item) for item in tmp_list))
        keyword_serializer = KeywordTagSerializer(video.keywords.all().filter(query&(Q(is_approved='ACP')|Q(is_approved='CHK')|Q(is_approved='CLN'))).order_by('frame_in'),
                                                  context={"request": request}, many=True)
        index = 0
        for keyword in keyword_serializer.data:
            words = keyword['words']
            final_word_level = []
            comment = ''
            if Comment.objects.filter(object_id=keyword['id']):
                comment = Comment.objects.filter(object_id=keyword['id']).first().comment
            if keyword['word_level']:
                word_level = json.loads(keyword['word_level'])['words']
                for word in word_level:
                    if any([item in word['word'] for item in filter_list]):
                        final_word_level.append(word)
            keyword_serializer.data[index]['word_level'] = final_word_level
            keyword_serializer.data[index]['words'] = words
            keyword_serializer.data[index]['tagname'] = 'profanity'
            keyword_serializer.data[index]['category'] = 'Compliance'
            keyword_serializer.data[index]['comment'] = comment
            index += 1
        final_data = compliance_tags_serializer.data
        final_data += keyword_serializer.data
        final_data = sorted(final_data, key=itemgetter('frame_in'))

        # users
        recipients = []
        for g in groups.split(","):
            users = User.objects.filter(Q(groups__name=g)).distinct()
            recipients += list(i for i in users.values_list('email', flat=True) if bool(i))
        recipients += emails.split(',')
        recipients_set = set(recipients)
        recipients_list = list(recipients_set)
        csv_file = '/tmp/{}.csv'.format(video.title.replace(".mp4",""))
        with open(csv_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if final_data:
                writer.writerow(["Overall Status", "Rejected"])
                c_tag, c = ComplianceStatusTag.objects.get_or_create(video=video)
                c_tag.is_approved = 'NCP'
                c_tag.save()
            else:
                writer.writerow(["Overall Status", "Accepted"])
                c_tag, c = ComplianceStatusTag.objects.get_or_create(video=video)
                c_tag.is_approved = 'ACP'
                c_tag.save()

            for tag in final_data:
                time_in = (str(timedelta(seconds=math.floor(tag['frame_in'] / video.frame_rate))) + ":" + (str(
                    tag['frame_in'] - math.floor(
                        video.frame_rate * math.floor(tag['frame_in'] / video.frame_rate)))).zfill(2)).zfill(11)
                time_out = (str(timedelta(seconds=math.floor(tag['frame_out'] / video.frame_rate))) + ":" + (str(
                    tag['frame_out'] - math.floor(
                        video.frame_rate * math.floor(tag['frame_out'] / video.frame_rate)))).zfill(2)).zfill(11)
                if 'word_level' in tag:
                    for word in tag['word_level']:
                        time_in = (str(timedelta(
                            seconds=math.floor(word['start_time'] + (tag['frame_in'] / video.frame_rate)))) + ":" + (
                            str(math.floor(video.frame_rate * word['start_time'] + tag['frame_in']) - math.floor(
                                video.frame_rate * math.floor(
                                    word['start_time'] + (tag['frame_in'] / video.frame_rate))))).zfill(2)).zfill(11)
                        time_out = (str(timedelta(
                            seconds=math.floor(word['end_time'] + (tag['frame_in'] / video.frame_rate)))) + ":" + (
                            str(math.floor(video.frame_rate * word['end_time'] + tag['frame_in']) - math.floor(
                                video.frame_rate * math.floor(
                                    word['end_time'] + (tag['frame_in'] / video.frame_rate))))).zfill(2)).zfill(11)
                        writer.writerow([time_in, time_out, word['word'], tag['comment']])
                else:
                    writer.writerow([time_in, time_out, tag['words']])
        email = EmailMessage(
            'Compliance Report for {}'.format(video.title),
            'Please Find attached the compliance report file\n\n',
            'aswin@tessact.com',
            recipients_list
        )
        email.attach_file(csv_file)
        email.send()

        return Response({"email_status": "success"}, status=status.HTTP_200_OK)

    def get_cognitive_face_data(self, video_id):
        video = Video.objects.filter(id=video_id).first()
        if video:
            fps = video.frame_rate
            data = []
            fg = FaceGroup.objects.all().filter(Q(video=video) & Q(person__isnull=False)).values("person__name").distinct()
            for p in fg:
                final_timeline = [0] * int(math.ceil(video.duration))
                person_name = p['person__name']
                fgs = FaceGroup.objects.all().filter(Q(video=video) & Q(person__name=person_name))
                for f in fgs:
                    timeline = f.timeline
                    for ind in range(int(len(timeline) / 2)):
                        t1 = timeline[ind * 2]
                        t2 = timeline[ind * 2 + 1]
                        final_timeline[t1: t2+1] =[1]*(t2+1-t1)
                print_timeline = []
                index = 0
                duration = 0
                for f in final_timeline:
                    if f==1:
                        duration += 1
                        if print_timeline:
                            # check for continuity
                            if print_timeline[-1][1]==index-1 or print_timeline[-1][1]==index:
                                print_timeline[-1][1]=index
                            elif print_timeline[-1][1]<index:
                                print_timeline.append([index, index+1])
                        else:
                            print_timeline.append([index, index+1])
                    index+=1
                percent = duration*100/video.duration
                data.append([person_name, "", "", duration, "{0:.2f}".format(percent)])
                for t in print_timeline:
                    data.append(["", sec2TCR(t[0], fps), sec2TCR(t[1] + 1, fps)])
            return data
        return None

    def get_cognitive_emotion_data(self, video_id):

        video = Video.objects.filter(id=video_id).first()
        frame_rate = video.frame_rate
        tags = video.emotiontag_set.all().values("emotion_quo").distinct()
        if tags:
            data = []
            for tag in tags:
                name = tag['emotion_quo']
                emotiontags = video.emotiontag_set.all().order_by('frame_in').filter(emotion_quo=name).values("frame_in", "frame_out").distinct()
                dur = 0
                timeline = []
                for lt in emotiontags:
                    timeline.append(["",  sec2TCR(lt['frame_in'], frame_rate),  sec2TCR(lt['frame_out'], frame_rate), "", "" ])
                    dur += (lt['frame_out']-lt['frame_in'])/frame_rate
                data.append([name, "", "", format(dur, '.2f'), "{0:.2f}".format(dur*100/video.duration)])
                data.extend(timeline)

            return data
            
        else:
            video_instance = video
            faces = Face.objects.filter(face_group__video=video_instance)
            time_line_not_sorted = {}
            time_line_filtered = {}

            for face in faces:
                video_frame = VideoFrame.objects.get(frame=face.face_rect.frame)
                try:
                    time_line_not_sorted[face.emotion].append(int(video_frame.time))
                except KeyError:
                    time_line_not_sorted[face.emotion] = [int(video_frame.time)]

            for td in time_line_not_sorted:
                time_line_filtered[td] = []
                for t in sorted(time_line_not_sorted[td]):
                    if not time_line_filtered[td]:
                        time_line_filtered[td].append(t)
                        time_line_filtered[td].append(t + 1)
                    elif t - 2 <= time_line_filtered[td][-1] <= t:
                        time_line_filtered[td][-1] = t
                    elif time_line_filtered[td][-1] > t:
                        continue
                    else:
                        time_line_filtered[td].append(t)
                        time_line_filtered[td].append(t + 1)
            output = []
            for td in time_line_filtered:
                timeline = time_line_filtered[td]
                modified_timeline = []
                dur = 0
                for i in range(int(len(timeline) / 2)):
                    modified_timeline.append(["" , sec2TCR(timeline[i * 2], frame_rate), sec2TCR(timeline[i * 2 + 1] + 1, frame_rate), "", ""])
                    dur += timeline[i * 2 + 1] - timeline[i * 2]
                if td == "sadness":
                    td="sad"
                elif td == "happiness":
                    td='happy'
                output.append([td, "", "", dur, "{0:.2f}".format(dur*100/video_instance.duration)])
                output.extend(modified_timeline)

            return output

    def get_cognitive_object_data(self, video_id):
        video = Video.objects.filter(id=video_id).first()
        if video:
            fps = video.frame_rate
            tags = video.frametag.all().values("tag__title").distinct()
            data = []
            for tag in tags:
                name = tag['tag__title']
                frametags = video.frametag.all().order_by('frame_in').filter(tag__title=name).values("frame_in", "frame_out").distinct()
                dur = 0
                data_header = [name, "", ""]
                timeline = []
                for lt in frametags:
                    timeline.append(['', sec2TCR(lt['frame_in']/fps, fps), sec2TCR(lt['frame_out']/fps, fps)])
                    dur += (lt['frame_out']-lt['frame_in'])/fps
                percent = dur*100/video.duration
                data_header.extend([int(dur), percent])
                data.append(data_header)
                data.extend(timeline)
            return data
        return None

    def get_cognitive_location_data(self, video_id):
        video = Video.objects.filter(id=video_id).first()
        if video:
            fps = video.frame_rate
            tags = video.manualtag.filter(tags__parent__title="Location").values("tags__title").distinct()
            data = []
            for tag in tags:
                name = tag['tags__title']
                frametags = video.manualtag.all().order_by('frame_in').filter(tags__title=name, tags__parent__title="Location")
                dur = 0
                data_header = [name, "", ""]
                timeline = []
                for lt in frametags:
                    timeline.append(['', sec2TCR(lt.frame_in/fps, fps), sec2TCR(lt.frame_out/fps, fps)])
                    dur += (lt.frame_out-lt.frame_in)/lt.video.frame_rate
                percent = dur*100/video.duration
                data_header.extend([int(dur), percent])
                data.append(data_header)
                data.extend(timeline)
            return data
        return None

    @detail_route(methods=['get'])
    def get_cognitive_report(self, request, pk=None):

        video_id = str(self.get_object().id)
        face_data = self.get_cognitive_face_data(video_id)
        emotion_data = self.get_cognitive_emotion_data(video_id)
        object_data = self.get_cognitive_object_data(video_id)
        location_data = self.get_cognitive_location_data(video_id)

        if face_data:
            face_df = pd.DataFrame(face_data, columns=["Character", "Start Time", "End Time", "Duration", "Percent"])
        else:
            face_df = pd.DataFrame(['', '', '', '', '', '', 'No Faces Found', '', '', '', '', '', '', '']).T


        if emotion_data:
            emotion_df = pd.DataFrame(emotion_data, columns=["Emotion", "Start Time", "End Time", "Duration", "Percent"])
        else:
            emotion_df = pd.DataFrame(['', '', '', '', '', '', 'No Emotion Found', '', '', '', '', '', '', '']).T


        if object_data:
            object_df = pd.DataFrame(object_data, columns=["Object", "Start Time", "End Time", "Duration", "Percent"])
        else:
            object_df = pd.DataFrame(['', '', '', '', '', '', 'No Objects Found', '', '', '', '', '', '', '']).T


        if location_data:
            location_df = pd.DataFrame(location_data, columns=["Location", "Start Time", "End Time", "Duration", "Percent"])
        else:
            location_df = pd.DataFrame(['', '', '', '', '', '', 'No Location Found', '', '', '', '', '', '', '']).T

        file_name = '/tmp/{}.xlsx'.format(video_id)
        zip_file_name = '/tmp/{}.zip'.format(video_id)
        writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
        face_df.to_excel(writer, sheet_name="Character")
        emotion_df.to_excel(writer, sheet_name="Emotion")
        object_df.to_excel(writer, sheet_name="Objects")
        location_df.to_excel(writer, sheet_name="Locations")
        writer.save()
        zipObj = zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED)
        zipObj.write(file_name, "CognitiveReport.xlsx")
        zipObj.close()
        os.remove(file_name)
        response = HttpResponse(open(zip_file_name, 'rb').read())
        os.remove(zip_file_name)
        return response

    @detail_route(methods=['get'])
    def send_moderation(self, request, pk=None):
        emails = request.query_params.get("emails", "aswin@tessact.com")
        groups = request.query_params.get("groups", "")

        video = self.get_object()
        send_moderation_report.delay(video.id, groups, emails, self.request.user.get_full_name())

        return Response({"email_status": "success"}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def send_keywords_excel(self, request, pk=None):
        emails = request.query_params.get("emails", "aswin@tessact.com")
        groups = request.query_params.get("groups", "")

        video = self.get_object()
        email_keywords_excel.delay(str(video.id), emails)

        return Response({"email_status": "success"}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def send_keywords_pdf(self, request, pk=None):
        emails = request.query_params.get("emails", "aswin@tessact.com")
        groups = request.query_params.get("groups", "")

        video = self.get_object()
        email_keywords_reportlab.delay(str(video.id), emails)

        return Response({"email_status": "success"}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_tags(self, request, pk =None):

        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Objects')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)

        return Response({"process id":str(auto.id)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_objects_aws(self, request, pk =None):

        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Objects AWS')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)

        return Response({"process id":str(auto.id)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_emotions_aws(self, request, pk =None):

        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Emotion AWS')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)

        return Response({"process id":str(auto.id)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_compliance(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Compliance')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": str(auto_url)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_compliance_audio(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Compliance Audio')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": str(auto_url)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_nudity(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Detect Nudity')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": str(auto_url)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_drugs(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Drugs')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": str(auto_url)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_smoking(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Smoking')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": str(auto_url)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_alcohol(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Alcohol')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": str(auto_url)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_sexdolls(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Sex Dolls')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": str(auto_url)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_fire(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Fire')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": str(auto_url)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_flag(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Indian Flag')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": str(auto_url)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_location(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Locations')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": str(auto_url)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_statue(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Naked Statue')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": str(auto_url)}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_hard_cuts(self, request, pk=None):
        video_instance = self.get_object()
        # call the method from the backend
        job_type_instance, _ = JobType.objects.get_or_create(name='Generate Hardcuts')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)

        video_serializer = CreateVideoSerializer(video_instance, partial=True)
        video_file = video_serializer.data['file']
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        # background_video_processing_hardcuts.delay(video_file, video_serializer.data['id'])
        return Response({"message": "process started"}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_logos(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Logos')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_samosas(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Find Samosas')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        background_video_processing_samosa.delay(video_instance.file, video_instance.id, auto.id)
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_face_detect(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Faces')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_emotion(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Emotion')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_trivia(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Trivia')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_keywords(self, request, pk=None):
        query_params = request.query_params
        lang = query_params.get('lang', 'en-US')
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Find Keywords')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        backgroundprocess_keywords.delay(video_instance.file, video_instance.id, auto.id, lang)

        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_keywords_hi(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Find Keywords Hindi')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_sentiment_en(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Find Keywords English With Sentiment')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_sentiment_hi(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Find Keywords Hindi With Sentiment')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_sentiment_mr(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Find Keywords Marathi With Sentiment')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_face_matching(self, request, pk=None):
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Match Faces')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_text_detection(self, request, pk=None):
        # query_params
        query_params = request.query_params
        time_in = query_params.get('time_in', None)
        time_out = query_params.get('time_out', None)
        lang = query_params.get('lang', 'en')
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Detect Text')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        background_detect_text.delay(video_instance.file, video_instance.id, auto.id, float(time_in) if time_in else None, float(time_out) if time_out else None, lang)
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def process_for_rolling_credits(self, request, pk=None):
        # query_params
        query_params = request.query_params
        time_in = query_params.get('time_in', None)
        time_out = query_params.get('time_out', None)
        video_instance = self.get_object()
        job_type_instance, _ = JobType.objects.get_or_create(name='Detect Rolling Credits')
        auto = AutoVideoJob.objects.create(created_by=self.request.user, video=video_instance,
                                           job_type=job_type_instance, eta=0)
        auto.save()
        background_rolling_credit.delay(video_instance.file, video_instance.id, auto.id, float(time_in) if time_in else None, float(time_out) if time_out else None)
        auto_url = AutoVideoJobSerializer(auto, context={"request": request}).data['url']
        return Response({"process url": auto_url}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def get_video_url(self, request):
        ext = request.query_params.get('ext', 'mp4')
        blob_url, token = self.generate_blob_sas(ext)
        return Response(data={"blob_url": blob_url, "token": token})

    @list_route(methods=['get'])
    def get_srt_url(self, request):
        blob_url, token = self.generate_blob_sas('srt')
        return Response(data={"blob_url": blob_url, "token": token})

    @list_route(methods=['get'])
    def get_stl_url(self, request):
        blob_url, token = self.generate_blob_sas('stl')
        return Response(data={"blob_url": blob_url, "token": token})

    def generate_blob_sas(self, ext):
        block_blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME, account_key=settings.AZURE_ACCOUNT_KEY)
        video_name = "{}.{}".format(uuid.uuid4(), ext)
        block_blob_service.create_blob_from_bytes(settings.AZURE_CONTAINER, video_name, b'')
        token = block_blob_service.generate_blob_shared_access_signature(settings.AZURE_CONTAINER, video_name,
                                                                         BlobPermissions.WRITE,
                                                                         datetime.utcnow() + timedelta(hours=1))
        full_path = "https://" + settings.AZURE_ACCOUNT_NAME + ".blob.core.windows.net/" + settings.AZURE_CONTAINER + \
                    "/" + video_name
        return [full_path, token]

    @list_route(methods=['get'])
    def search_video(self, request):
        logger.debug(request.query_params.get("audio", None))
        audio_search_term = request.query_params.get("audio", None)
        text_search_term = request.query_params.get("text", None)
        visual_search_term = request.query_params.get("visual", None)

        # search terms with keywords
        if audio_search_term:
            audio_search_term = audio_search_term.lower()
            keywords_filter_queries = [Q(keywords__words__contains=term)|Q(keywords__words__contains=term.capitalize()) for term in audio_search_term.split(' ')]
            keywords_filter_query = keywords_filter_queries.pop()
            for item in keywords_filter_queries:
                keywords_filter_query |= item
            keywords_search_queries = [SearchQuery(term)|SearchQuery(term.capitalize()) for term in audio_search_term.split("+")]
            keywords_search_query = keywords_search_queries.pop()
            for item in keywords_search_queries:
                keywords_search_query |= item

        else:
            keywords_search_query = None
            keywords_filter_query = None

        # search terms with title
        if text_search_term:
            text_search_term=text_search_term.lower()
            text_filter_queries = [Q(title__contains=term)|Q(title__contains=term.capitalize()) for term in text_search_term.split(' ')]
            text_filter_query = text_filter_queries.pop()
            for item in text_filter_queries:
                text_filter_query |= item
            text_search_queries = [SearchQuery(term)|SearchQuery(term.capitalize()) for term in text_search_term.split("+")]
            text_search_query = text_search_queries.pop()
            for item in text_search_queries:
                text_search_query |= item
        else:
            text_search_query = None
            text_filter_query = None

        # search with visual keywords
        # create filters for facegroups and frametags
        if visual_search_term:
            visual_search_term=visual_search_term.lower()
            visual_filter_queries = [Q(facegroup__person__name__icontains=term)|Q(frametag__tag__name__contains=term)|Q(frametag__tag__name__contains=term.capitalize()) for term in visual_search_term.split(' ')]
            visual_filter_query = visual_filter_queries.pop()
            for item in visual_filter_queries:
                visual_filter_query |= item
        else:
            visual_filter_query = None

        combined_filter_queries = [text_filter_query, keywords_filter_query, visual_filter_query]
        combined_filter_queries = list(filter(lambda x: x, combined_filter_queries))
        if combined_filter_queries:
            filter_query = reduce((lambda x, y: x | y), combined_filter_queries)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        qs = Video.objects.filter(filter_query).distinct()
        if keywords_search_query:
            qs = qs.annotate(match=Headline(StringAgg('keywords__words', delimiter=' '), keywords_search_query, options="MaxFragments=3, MaxWords=50, MinWords=35"))
        if text_search_query:
            qs = qs.annotate(title_highlight=Headline(F('title'), text_search_query))
        video_search_objects = qs
        serializer = SearchVideoSerializer(video_search_objects, many=True, context={"request": request})
        # else:
        #     serializer = SearchVideoWithoutMatchSerializer(video_search_objects, many=True, context={"request":request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @list_route(methods=['post'])
    def label_it(self, request):
        url = request.query_params.get("url", None)
        if url:
            content = requests.get(url).content
            client = vision.ImageAnnotatorClient()
            image = types.Image(content=content)

            # labels
            response = client.label_detection(image=image)
            labels = response.label_annotations
            f_labels = []
            for label in labels:
                f_labels.append(label.description)

            # ocr
            response = client.text_detection(image=image)
            texts = response.text_annotations

            for text in texts:
                print('\n"{}"'.format(text.description))

            # faces
            response = client.face_detection(image=image)
            faces = response.face_annotations
            num_faces = len(faces)
            hit = False
            if "actor" or "film" in f_labels or num_faces == 0:
                hit = True
            final_text = texts[0].description if len(texts) else "None"
            return Response(data={"visual": f_labels, "text":final_text, "faces": num_faces}, status=status.HTTP_200_OK)

    def label_it(self, request):
        url = request.query_params.get("url", None)
        if url:
            content = requests.get(url).content
            client = vision.ImageAnnotatorClient()
            image = types.Image(content=content)

            # labels
            response = client.label_detection(image=image)
            labels = response.label_annotations
            f_labels = []
            for label in labels:
                f_labels.append(label.description)

            # ocr
            response = client.text_detection(image=image)
            texts = response.text_annotations

            for text in texts:
                print('\n"{}"'.format(text.description))

            # faces
            response = client.face_detection(image=image)
            faces = response.face_annotations
            num_faces = len(faces)
            hit = False
            if "actor" or "film" in f_labels or num_faces == 0:
                hit = True
            final_text = texts[0].description if len(texts) else "None"
            return Response(data={"visual": f_labels, "text":final_text, "faces": num_faces}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def get_edl_status(self, request, pk=None):
        id = request.query_params.get("id",None)
        mobj = MasterReportGen.objects.filter(id=id).first()
        if mobj:
            return Response(data={"results": MasterReportGenSerializer(mobj, context={"request": request}).data}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def get_edl(self, request, pk=None):
        videos = request.query_params.get("video", None)
        id = request.query_params.get("id",None)
        collection = request.query_params.get("collection", None)
        type_ = request.query_params.get("type", None)
        is_indexed = request.query_params.get("is_indexed", None)
        is_indexed = None if not is_indexed else (True if is_indexed and is_indexed == "true" else False)

        if not id:
            m = MasterReportGen.objects.create()
            generate_edl.delay(id=m.id, videos=videos, collection=collection, type_=type_, is_indexed=is_indexed, username=request.user.username)
            return Response(data={"id":m.id}, status=status.HTTP_200_OK)
        else:
            mobj = MasterReportGen.objects.filter(id=id).first()
            if mobj:
                zipObj = zipfile.ZipFile('/tmp/{}.zip'.format(id), 'w', zipfile.ZIP_DEFLATED)
                zipObj.write('/tmp/EDL-comments.csv', 'EDL-comments.csv')
                zipObj.write('/tmp/EDL.edl', 'EDL.edl')
                zipObj.close()
                os.remove('/tmp/EDL-comments.csv')
                os.remove('/tmp/EDL.edl')
                file_name = "/tmp/{}.zip".format(id)
                response = HttpResponse(open(file_name, 'rb').read())
                # os.remove('/tmp/{}.zip'.format(id))
                return response

    @list_route(methods=['post'])
    def search_edl(self, request, pk=None):
        try:
            object_dict = json.loads(request.body.decode('utf-8'))
            logging.info(object_dict)
        except:
            pass
        id = request.query_params.get("id",None)
        if not id:
            m = MasterReportGen.objects.create()
            generate_search_edl.delay(id=m.id, object_dict=object_dict)
            return Response(data={"id":m.id}, status=status.HTTP_200_OK)
        # else:
        #     mobj = MasterReportGen.objects.filter(id=id).first()
        #     if mobj:
        #         zipObj = zipfile.ZipFile('/tmp/{}.zip'.format(id), 'w', zipfile.ZIP_DEFLATED)
        #         zipObj.write('/tmp/{}.edl'.format(id))
        #         zipObj.close()
        #         os.remove("/tmp/{}.edl".format(id))
        #         file_name = "/tmp/{}.zip".format(id)
        #         response = HttpResponse(open(file_name, 'rb').read())
        #         os.remove('/tmp/{}.zip'.format(id))
        #         return response

    @list_route(methods=['get'])
    def get_search_edl(self, request, pk=None):
        id = request.query_params.get("id",None)
        if id:
            mobj = MasterReportGen.objects.filter(id=id).first()
            if mobj:
                zipObj = zipfile.ZipFile('/tmp/{}.zip'.format(id), 'w', zipfile.ZIP_DEFLATED)
                zipObj.write('/tmp/{}.edl'.format(id))
                zipObj.close()
                os.remove("/tmp/{}.edl".format(id))
                file_name = "/tmp/{}.zip".format(id)
                response = HttpResponse(open(file_name, 'rb').read())
                os.remove('/tmp/{}.zip'.format(id))
                return response

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'])
    def uploadFile(self, request):
        """
        The initial post request includes the filename
        and auth credientails. In our case, we'll use
        Session Authentication but any auth should work.
        """
        title = request.data.get('title')
        if not title:
                return Response({"message": "A filename is required"}, status=status.HTTP_400_BAD_REQUEST)
        policy_expires = int(time.time()+5000)

        """
        Below we create the Django object. We'll use this
        in our upload path to AWS.

        Example:
        To-be-uploaded file's name: Some Random File.mp4
        Eventual Path on S3: <bucket>/username/2312/2312.mp4
        """
        file_obj = Video.objects.create(title=title)
        file_obj_id = file_obj.id
        upload_start_path = "{uploads}/".format(
                    uploads = "uploads"
            )
        _, file_extension = os.path.splitext(title)
        filename_final = "{file_obj_id}{file_extension}".format(
                    file_obj_id= file_obj_id,
                    file_extension=file_extension
                )
        """
        Eventual file_upload_path includes the renamed file to the
        Django-stored FileItem instance ID. Renaming the file is
        done to prevent issues with user generated formatted names.
        """
        final_upload_path = "{upload_start_path}{filename_final}".format(
                                 upload_start_path=upload_start_path,
                                 filename_final=filename_final,
                            )
        if title and file_extension:
            """
            Save the eventual path to the Django-stored FileItem instance
            """
            file_obj.file = final_upload_path
            file_obj.save()

        policy_document_context = {
            "expire": policy_expires,
            "bucket_name": AWS_UPLOAD_BUCKET,
            "key_name": "",
            "acl_name": "private",
            "content_name": "",
            "content_length": 524288000,
            "upload_start_path": upload_start_path,

            }
        policy_document = """
        {"expiration": "2019-01-01T00:00:00Z",
          "conditions": [
            {"bucket": "%(bucket_name)s"},
            ["starts-with", "$key", "%(upload_start_path)s"],
            {"acl": "%(acl_name)s"},

            ["starts-with", "$Content-Type", "%(content_name)s"],
            ["starts-with", "$filename", ""],
            ["content-length-range", 0, %(content_length)d]
          ]
        }
        """ % policy_document_context
        aws_secret = str.encode(AWS_UPLOAD_SECRET_KEY)
        policy_document_str_encoded = str.encode(policy_document.replace(" ", ""))
        url = 'https://{bucket}.s3-{region}.amazonaws.com/'.format(
                        bucket=AWS_UPLOAD_BUCKET,
                        region=AWS_UPLOAD_REGION
                        )
        policy = base64.b64encode(policy_document_str_encoded)
        signature = base64.b64encode(hmac.new(aws_secret, policy, hashlib.sha1).digest())
        data = {
            "policy": policy,
            "signature": signature,
            "key": AWS_UPLOAD_ACCESS_KEY_ID,
            "file_bucket_path": upload_start_path,
            "file_id": file_obj_id,
            "filename": filename_final,
            "url": url
        }
        return Response(data, status=status.HTTP_200_OK)


class VideoLibraryViewSet(CacheResponseMixin, viewsets.ModelViewSet):
    serializer_class = VideoLibrarySerializer
    permission_classes = (permissions.IsAuthenticated, )
    queryset = VideoLibrary.objects.all()


class AudioViewSet(viewsets.ModelViewSet):
    serializer_class = AudioSerializer
    permission_classes = (permissions.IsAuthenticated, )
    queryset = Audio.objects.all()

    @list_route(methods=['get'])
    def get_audio_url(self, request):
        blob_url, token = self.generate_blob_sas()
        return Response(data={"blob_url": blob_url, "token": token})

    def generate_blob_sas(self):
        block_blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME,
                                              account_key=settings.AZURE_ACCOUNT_KEY)
        video_name = "{}.{}".format(uuid.uuid4(), 'mp3')
        block_blob_service.create_blob_from_bytes(settings.AZURE_CONTAINER, video_name, b'')
        token = block_blob_service.generate_blob_shared_access_signature(settings.AZURE_CONTAINER, video_name,
                                                                         BlobPermissions.WRITE,
                                                                         datetime.utcnow() + timedelta(hours=1))
        full_path = "https://" + settings.AZURE_ACCOUNT_NAME + ".blob.core.windows.net/" + settings.AZURE_CONTAINER + \
                    "/" + video_name
        return [full_path, token]


class SignedUrlViewershipViewset(viewsets.ModelViewSet):

    @list_route(methods=['get', 'post'])
    def multiple_signed_url(self, request, pk=None):
        video_ids = json.loads(request.body.decode('utf-8'))
        videos = Video.obejcts.filter(id__in=video_ids)
        signed_urls = [{'id': str(x.id), "signed_url": s3_signed_url(x.file, x.title)} for x in videos]
        return Response(data={"signed_urls": signed_urls}, status=status.HTTP_200_OK)

class TranscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = TranscriptionSerializer
    permission_classes = (permissions.IsAuthenticated, )
    queryset = Transcription.objects.all()

    @list_route(methods=['get'])
    def get_text_url(self, request):
        blob_url, token = self.generate_blob_sas()
        return Response(data={"blob_url": blob_url, "token": token})

    def generate_blob_sas(self):
        block_blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME,
                                              account_key=settings.AZURE_ACCOUNT_KEY)
        video_name = "{}.{}".format(uuid.uuid4(), 'txt')
        block_blob_service.create_blob_from_bytes(settings.AZURE_CONTAINER, video_name, b'')
        token = block_blob_service.generate_blob_shared_access_signature(settings.AZURE_CONTAINER, video_name,
                                                                         BlobPermissions.WRITE,
                                                                         datetime.utcnow() + timedelta(hours=1))
        full_path = "https://" + settings.AZURE_ACCOUNT_NAME + ".blob.core.windows.net/" + settings.AZURE_CONTAINER + \
                    "/" + video_name
        return [full_path, token]


class SubtitleViewSet(viewsets.ModelViewSet):
    serializer_class = SubtitleSerializer
    permission_classes = (permissions.IsAuthenticated, )
    queryset = Subtitle.objects.all()

    @list_route(methods=['get'])
    def get_subtitle_url(self, request):
        blob_url, token = self.generate_blob_sas()
        return Response(data={"blob_url": blob_url, "token": token})

    def generate_blob_sas(self):
        block_blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME,
                                              account_key=settings.AZURE_ACCOUNT_KEY)
        srt_name = "{}.{}".format(uuid.uuid4(), 'srt')
        block_blob_service.create_blob_from_bytes(settings.AZURE_CONTAINER, srt_name, b'')
        token = block_blob_service.generate_blob_shared_access_signature(settings.AZURE_CONTAINER, srt_name,
                                                                         BlobPermissions.WRITE,
                                                                         datetime.utcnow() + timedelta(hours=1))
        full_path = "https://" + settings.AZURE_ACCOUNT_NAME + ".blob.core.windows.net/" + settings.AZURE_CONTAINER + \
                    "/" + srt_name
        return [full_path, token]

class VideoSubtitleViewSet(viewsets.ModelViewSet):
    serializer_class = VideoSubtitleSerializer
    queryset = VideoSubtitle.objects.all()

    action_serializer_classes = {
        "create": CreateVideoSubtitleSerializer,
        "retrieve": DetailVideoSubtitleSerializer
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(VideoSubtitleViewSet, self).get_serializer_class()

class VideoProxyPathViewSet(viewsets.ModelViewSet):
    serializer_class = VideoProxyPathSerializer
    permission_classes = (permissions.IsAuthenticated, )
    queryset = VideoProxyPath.objects.all()

    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ("metadata","nbm","sourceproxy")

    @list_route(methods=['get'])
    def get_report_status(self, request, pk=None):
        id = request.query_params.get("id",None)
        mobj = MasterReportGen.objects.filter(id=id).first()
        if mobj:
            return Response(data={"results": MasterReportGenSerializer(mobj, context={"request": request}).data}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def get_report(self, request, pk=None):
        """ CHANNEL AND DATE RANGE ARE MANDATORY PAARAMETERS"""
        channel = request.query_params.get("channel", None)
        date_range = request.query_params.get("date", None)
        id = request.query_params.get("id", None)
        content_type = request.query_params.get("content_type", None)
        type_ = request.query_params.get("type", None)

        if not id:
            if content_type is None or date_range is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            m = MasterReportGen.objects.create()
            send_ingest_report.delay(id=m.id, date_range=date_range, channel=channel, username=request.user.username, content_type=content_type, type=type_)
            return Response(data={"id":m.id}, status=status.HTTP_200_OK)
        else:
            mobj = MasterReportGen.objects.filter(id=id).first()
            if mobj:
                zipObj = zipfile.ZipFile('/tmp/{}.zip'.format(id), 'w', zipfile.ZIP_DEFLATED)
                zipObj.write('/tmp/{}.csv'.format(id))
                zipObj.close()
                os.remove("/tmp/{}.csv".format(id))
                file_name = "/tmp/{}.zip".format(id)
                response = HttpResponse(open(file_name, 'rb').read())
                os.remove('/tmp/{}.zip'.format(id))
                return response

    # @list_route(methods=['get'])
    # def get_report(self, request):
    #     user = self.request.user
    #     query_params = request.query_params
    #     dates = query_params.get('dates', None)
    #     start_date = dates.split("_")[0]
    #     end_date = dates.split("_")[1]
    #     group = query_params.get('group', None)
    #     file_format = query_params.get('file_format', None)

    #     if file_format == 'pdf':
    #         # Create the HttpResponse object with the appropriate PDF headers.
    #         response = HttpResponse(content_type='application/pdf')
    #         response['Content-Disposition'] = 'attachment; filename="Report.pdf"'
    #         buffer = BytesIO()

    #         report = NX_report(buffer, 'Letter')
    #         pdf = report.ingest_status_report(user, start_date, end_date, file_format)
    #         response.write(pdf)
    #     else:
    #         logging.info(file_format)
    #         send_ingest_report.delay(start_date, end_date, group, file_format)
    #         return Response(data={"status": "started"}, status=status.HTTP_200_OK)

        return response

class ClipViewSet(viewsets.ModelViewSet):
    serializer_class = ClipSerializer
    permission_classes = (permissions.IsAuthenticated, )
    queryset = Clip.objects.all()

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = (permissions.IsAuthenticated, )
    queryset = Ticket.objects.all()

class CreateEndpointViewset(viewsets.ViewSet):

    def list(self, request):
        create_all_endpoints.delay()
        return Response(data={'Trigger': "done"})

class DeleteEndpointViewset(viewsets.ViewSet):
    def list(self, request):
        delete_all_endpoints.delay()
        return Response(data={'Trigger': "done"})


class SetThumbnail(APIView):
    """
    updating video thumbnail
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        video_id = request.data['video']
        v_time = request.data['time']
        set_thumbnail.delay(video_id, v_time)
        return Response(data={'success': 'done'})