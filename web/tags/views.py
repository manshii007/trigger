#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from rest_framework.viewsets import ModelViewSet
from django.core.exceptions import MultipleObjectsReturned
from rest_framework.decorators import detail_route, list_route
from rest_framework import (
    status,
    response,
    permissions,
    filters
)
import math
import django_filters
from django.conf import settings
from django.core.mail import send_mail
import datetime
from urllib.parse import unquote
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from rest_framework.response import Response
from rest_framework_extensions.key_constructor.bits import (
    KeyBitBase,
    ListSqlQueryKeyBit,
    RetrieveSqlQueryKeyBit,
    PaginationKeyBit,
    UserKeyBit
)
from django.http import HttpResponse
from django.template import loader
import csv, os
from django.utils.encoding import force_text
from django.core.cache import cache
from django.db.models import Q
from itertools import chain
from .pagination import StandardResultsSetPagination, ShortResultsSetPagination
from video.models import Video
from content.models import ChannelClip, Song
from content.tasks import send_mct
from .models import (
    Marker,
    Tag,
    TagCategory,
    FrameTag,
    CheckTag,
    CorrectionTag,
    KeywordTag,
    SceneTag,
    Logo,
    LogoTag,
    ComplianceStatusTag,
    PromoCategory,
    BarcTag,

    ProgramGenre,
    ProgramTheme,
    Advertiser,
    AdvertiserGroup,
    BrandName,
    BrandSector,
    BrandCategory,
    Title,
    Descriptor,
    Channel,
    ChannelNetwork,
    ChannelGenre,
    Region,
    ContentLanguage,
    ProductionHouse,
    Program,
    Promo,
    Commercial,
    PlayoutTag,
    SpriteTag,
    CommercialTag,
    GenericTag,
    ManualTag,
    ManualTagQCStatus,
)
from .serializers import (
    CheckTagSerializer,
    CreateCheckTagSerializer,
    CorrectionTagSerializer,
    CreateCorrectionTagSerializer,
    TagCategorySerializer,
    TagSerializer,
    FrameTagSerializer,
    CreateFrameTagSerializer,
    TagByCategorySerializer,
    SceneTagSerializer,
    KeywordTagSerializer,
    LogoSerializer,
    LogoTagSerializer,
    ComplianceStatusSerializer,
    BarcTagSerializer,
    PromoCategorySerializer,
    CreateBarcTagSerializer,
    CreateTitleSerializer,
    ProgramThemeSerializer,
    ProgramGenreSerializer,
    AdvertiserGroupSerializer,
    AdvertiserSerializer,
    BrandCategorySerializer,
    BrandSectorSerializer,
    BrandNameSerializer,
    TitleSerializer,
    DescriptorSerializer,
    ChannelSerializer,
    ChannelNetworkSerializer,
    ChannelGenreSerializer,
    RegionSerializer,
    ContentLanguageSerializer,
    ProductionHouseSerializer,
    ProgramSerializer,
    PromoSerializer,
    CommercialSerializer,
    PlayoutTagSerializer,
    CreatePlayoutTagSerializer,
    DetailCommercialSerializer,
    DetailProgramSerializer,
    DetailPromoSerializer,
    DetailAdvertiserSerializer,
    DetailBrandCategorySerializer,
    DetailBrandNameSerializer,
    DetailProgramGenreSerializer,
    SpriteTagSerializer,
    CommercialTagSerializer,
    CreateDescriptorSerializer,
    CreateAdvertiserGroupSerializer,
    CreateBrandCategorySerializer,
    CreateBrandSectorSerializer,
    TDetailCommercialSerializer,
    TDetailProgramSerializer,
    TDetailPromoSerializer,
    GenericTagSerializer,
    DetailGenericTagSerializer,
    ManualTagSerializer,
    CreateManualTagSerializer,
    ManualTagQCStatusSerializer,
    FrameTagCollectionSerializer,
    MarkerSerializer,
)
from .filters import (
    TagCategoryFilter,
    TagFilter,
    FrameTagFilter,
    SceneTagFilter,
    KeywordTagFilter,
    ProgramFilter,
    PromoFilter,
    CommercialFilter,
    ManualTagFilter,
    GenericTagFilter
)
from masters.models import VendorCommercial, VendorMasterComparison, VendorProgram, VendorPromo, VendorReportPromo,\
    VendorReportCommercial
from masters.serializers import  VendorReportCountSerializer
from django.db.models import Count
from content.models import Movie, Person
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework_tracking.models import APIRequestLog
from rest_framework.permissions import IsAuthenticated, IsAdminUser
import urllib.parse
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


class TagUpdatedAtKeyBit(KeyBitBase):
    def get_data(self, **kwargs):
        key = 'tag_api_updated_at_timestamp'
        value = cache.get(key, None)
        if not value:
            value = datetime.datetime.utcnow()
            cache.set(key, value=value)
        return force_text(value)


class TagObjectKeyConstructor(DefaultKeyConstructor):
    retrieve_sql = RetrieveSqlQueryKeyBit()
    updated_at = TagUpdatedAtKeyBit()
    user = UserKeyBit()


class TagListKeyConstructor(DefaultKeyConstructor):
    list_sql = ListSqlQueryKeyBit()
    pagination = PaginationKeyBit()
    updated_at = TagUpdatedAtKeyBit()
    user = UserKeyBit()


class TagCategoryUpdatedAtKeyBit(KeyBitBase):
    def get_data(self, **kwargs):
        key = 'tag_category_api_updated_at_timestamp'
        value = cache.get(key, None)
        if not value:
            value = datetime.datetime.utcnow()
            cache.set(key, value=value)
        return force_text(value)


class TagCategoryObjectKeyConstructor(DefaultKeyConstructor):
    retrieve_sql = RetrieveSqlQueryKeyBit()
    updated_at = TagCategoryUpdatedAtKeyBit()
    user = UserKeyBit()


class TagCategoryListKeyConstructor(DefaultKeyConstructor):
    list_sql = ListSqlQueryKeyBit()
    pagination = PaginationKeyBit()
    updated_at = TagCategoryUpdatedAtKeyBit()
    user = UserKeyBit()


class TagCategoryViewSet(ModelViewSet):
    queryset = TagCategory.objects.all()
    serializer_class = TagCategorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_class = TagCategoryFilter
    search_fields = ('name',)
    action_serializer_classes = {
        "retrieve": TagByCategorySerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(TagCategoryViewSet, self).get_serializer_class()

    @cache_response(key_func=TagCategoryObjectKeyConstructor())
    def retrieve(self, *args, **kwargs):
        return super(TagCategoryViewSet, self).retrieve(*args, **kwargs)

    @cache_response(key_func=TagCategoryListKeyConstructor())
    def list(self, *args, **kwargs):
        return super(TagCategoryViewSet, self).list(*args, **kwargs)


class TagViewSet(ModelViewSet):
    """
    Lists, Creates, Updates, and Retrieves Global Tags
    """
    queryset = Tag.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TagSerializer
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_class = TagFilter
    search_fields = ('name',)

    @list_route()
    def by_category(self, request):
        tags_categories_queryset = TagCategory.objects.all()
        tags_by_category_serializer = TagByCategorySerializer(tags_categories_queryset, context={"request":request},
                                                              many=True)
        return response.Response(tags_by_category_serializer.data, status=status.HTTP_200_OK)

    @cache_response(key_func=TagObjectKeyConstructor())
    def retrieve(self, *args, **kwargs):
        return super(TagViewSet, self).retrieve(*args, **kwargs)

    @cache_response(key_func=TagListKeyConstructor())
    def list(self, *args, **kwargs):
        return super(TagViewSet, self).list(*args, **kwargs)

    @list_route(methods=['get'])
    def search_all(self, request):
        name = request.query_params.get('name')
        page = request.query_params.get('page')
        data = []
        tags = Tag.objects.filter(name__icontains=name)
        for tag in tags:
            data.append(
                {
                    "id": str(tag.id),
                    "name": tag.name,
                    "mode": "Tag"
                }
            )
        persons = Person.objects.filter(name__icontains=name)
        for person in persons:
            data.append(
                {
                    "id": str(person.id),
                    "name": person.name,
                    "mode": "Person"
                }
            )
        movies = Movie.objects.filter(movie_title__icontains=name)
        for movie in movies:
            data.append(
                {
                    "id": str(movie.id),
                    "name": movie.movie_title,
                    "mode": "Movie"
                }
            )
        return Response(data=data, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def search_pm(self, request):
        name = request.query_params.get('name')
        page = request.query_params.get('page')
        data = []
        spaced_name = " "+name
        persons = Person.objects.filter(Q(name__istartswith=name)|Q(name__icontains=spaced_name))
        for person in persons:
            data.append(
                {
                    "id": str(person.id),
                    "name": person.name,
                    "mode": "Person"
                }
            )
        movies = Movie.objects.filter(Q(movie_title__istartswith=name))
        for movie in movies:
            data.append(
                {
                    "id": str(movie.id),
                    "name": movie.movie_title,
                    "mode": "Movie"
                }
            )
        return Response(data=data, status=status.HTTP_200_OK)

class FrameTagViewSet(ModelViewSet):
    """
    Lists, Creates, Updates and retrieves Frame Tags
    """
    queryset = FrameTag.objects.all()
    serializer_class = FrameTagSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_class = FrameTagFilter
    search_fields = ('tag__title')
    action_serializer_classes = {
        "create": CreateFrameTagSerializer,
        "update": CreateFrameTagSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(FrameTagViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs): # To accomodate multiple object creation with a single request
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['get'])
    def fetchindexedframetags(self, request):
        videos = request.query_params.get('video')
        collection = request.query_params.get('collection')
        tags = None
        if videos and collection:
            #fetch frame tags for collection edl page
            videos = videos.split(",")
            if len(videos) == 1:
                tags = FrameTag.objects.filter(video__in=videos, collection=collection).order_by('frame_in')
            else:
                tags = FrameTag.objects.filter(video__in=videos, collection=collection).order_by('index')
        elif videos:
            #fetch frame tags for video edl page
            if len(videos.split(",")) == 1:
                tags = FrameTag.objects.filter(video=videos, collection=None, index__isnull=False).order_by('index')
            else:
                return Response(data={"response":"multiple videos"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
        else:
            return Response(data={"response": "failed"}, status=status.HTTP_400_BAD_REQUEST)
        tag_by_collection_videos_serialiser = FrameTagCollectionSerializer(tags, context={"request":request}, many=True)
        return response.Response(tag_by_collection_videos_serialiser.data, status=status.HTTP_200_OK)

    @list_route(methods=['post'])
    def editframetagindex(self, request):
        data = request.data
        if len(data) >= 1: 
            for frame_tag in data:
                frame_tag_obj = None
                frame_tag_obj = FrameTag.objects.filter(id=frame_tag['id']).first()
                if frame_tag_obj:
                    frame_tag_obj.index = frame_tag['index']
                    frame_tag_obj.save()
                else:
                    return Response(data={"response":"not a frame tag"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(data={"response": "success"}, status=status.HTTP_200_OK)
        return Response(data={"response": "failed"}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'])
    def delete_multiple(self, request, uuid=None):
        if not uuid:
            uuids = request.query_params.get('ids', None)
            uuids = uuids.split(",")
            if not uuids:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if len(uuids) != FrameTag.objects.filter(id__in=uuids).count():
                return Response(status=status.HTTP_404_NOT_FOUND)
            FrameTag.objects.filter(id__in=uuids).delete()
        else:
            instance = self.get_object(uuid)
            if not instance:
                return Response(status=status.HTTP_404_NOT_FOUND)
            instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CheckTagViewSet(ModelViewSet):
    """
    Lists, Creates, Updates and retrieves Frame Tags
    """
    queryset = CheckTag.objects.all()
    serializer_class = CheckTagSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    search_fields = ('autotag__title')
    action_serializer_classes = {
        "create": CreateCheckTagSerializer,
        "update": CreateCheckTagSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(CheckTagViewSet, self).get_serializer_class()

    def list(self, *args, **kwargs):
        return super(CheckTagViewSet, self).list(*args, **kwargs)

    def create(self, request, *args, **kwargs): # To accomodate multiple object creation with a single request
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

#    @list_route(methods=['get'])
#    def fetchindexedframetags(self, request):
#        videos = request.query_params.get('video')
#        tags = None
#        if videos:
#            #fetch frame tags for video edl page
#            if len(videos.split(",")) == 1:
#                tags = FrameTag.objects.filter(video=videos)
#            else:
#                return Response(data={"response":"multiple videos"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
#        else:
#            return Response(data={"response": "failed"}, status=status.HTTP_400_BAD_REQUEST)
#        tag_by_collection_videos_serialiser = FrameTagCollectionSerializer(tags, context={"request":request}, many=True)
#        return response.Response(tag_by_collection_videos_serialiser.data, status=status.HTTP_200_OK)

#    @list_route(methods=['post'])
#    def editframetagindex(self, request):
#        data = request.data
#        if len(data) >= 1: 
#            for frame_tag in data:
#                frame_tag_obj = None
#                frame_tag_obj = FrameTag.objects.filter(id=frame_tag['id']).first()
#                if frame_tag_obj:
#                    frame_tag_obj.index = frame_tag['index']
#                    frame_tag_obj.save()
#                else:
#                    return Response(data={"response":"not a frame tag"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#            return Response(data={"response": "success"}, status=status.HTTP_200_OK)
#        return Response(data={"response": "failed"}, status=status.HTTP_400_BAD_REQUEST)

class CorrectionTagViewSet(ModelViewSet):
    """
    Lists, Creates, Updates and retrieves Frame Tags
    """
    queryset = CorrectionTag.objects.all()
    serializer_class = CorrectionTagSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    action_serializer_classes = {
        "create": CreateCorrectionTagSerializer,
        "update": CreateCorrectionTagSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(CorrectionTagViewSet, self).get_serializer_class()

    def list(self, *args, **kwargs):
        return super(CorrectionTagViewSet, self).list(*args, **kwargs)

    def create(self, request, *args, **kwargs): # To accomodate multiple object creation with a single request
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class ManualTagViewSet(ModelViewSet):
    """
    Lists, Creates, Updates and retrieves Frame Tags
    """
    queryset = ManualTag.objects.all().order_by("frame_in")
    serializer_class = ManualTagSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_class = ManualTagFilter
    search_fields = ('tags__title',)
    action_serializer_classes = {
        "create": CreateManualTagSerializer,
        "update": CreateManualTagSerializer,
        "partial_update": CreateManualTagSerializer
    }
    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(ManualTagViewSet, self).get_serializer_class()

    def update(self, request, *args, **kwargs):
        """
        To cater the full object of foreign keys after update
        """
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = CreateManualTagSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        #Create QC status entry for every generic tag added to a manual tag
        existing_manual_tags_qc_qs = ManualTagQCStatus.objects.filter(manual_tag=instance)
        for tag in instance.tags.all():
            # if the tag exists in manual_tag_qc_status model keep it as is.
            if existing_manual_tags_qc_qs.filter(tag=tag).exists():
                existing_manual_tags_qc_qs = existing_manual_tags_qc_qs.exclude(tag=tag)
            else:
                ManualTagQCStatus.objects.create(tag=tag, manual_tag=instance, qc_approved=True)
                existing_manual_tags_qc_qs = existing_manual_tags_qc_qs.exclude(tag=tag) #because on generating it gets added to qs
        
        # remove the manual_tag_qc_status entry if the tag is removed  from manual tag.     
        if len(existing_manual_tags_qc_qs) > 0:
            existing_manual_tags_qc_qs.delete()
        complete_ser = CreateManualTagSerializer(ManualTag.objects.get(id=instance.id))
        return Response(complete_ser.data)

class KeywordTagViewSet(ModelViewSet):
    """
    Lists, Creates, Updates and retrieves Frame Tags
    """
    queryset = KeywordTag.objects.all()
    serializer_class = KeywordTagSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_class = KeywordTagFilter
    search_fields = ('words',)

    # def get_serializer_class(self):
    #     try:
    #         return self.action_serializer_classes[self.action]
    #     except (KeyError, AttributeError):
    #         return super(KeywordTagSerializer, self).get_serializer_class()


class SceneTagViewSet(ModelViewSet):
    queryset = SceneTag.objects.all()
    serializer_class = SceneTagSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_class = SceneTagFilter
    search_fields = ('characters__character_name', 'description')


class LogoViewSet(ModelViewSet):
    queryset = Logo.objects.all()
    serializer_class = LogoSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name',)


class PromoCategoryViewSet(ModelViewSet):
    queryset = PromoCategory.objects.all()
    serializer_class = PromoCategorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name',)


class LogoTagViewSet(ModelViewSet):
    """
    Lists, Creates, Updates and retrieves Frame Tags
    """
    queryset = LogoTag.objects.all()
    serializer_class = LogoTagSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    search_fields = ('tag__name',)


class ComplianceStatusViewSet(ModelViewSet):
    queryset = ComplianceStatusTag.objects.all()
    serializer_class = ComplianceStatusSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('video',)


class BarcTagViewSet(ModelViewSet):
    queryset = BarcTag.objects.all().order_by('video', 'frame_in')
    serializer_class = BarcTagSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = StandardResultsSetPagination
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('video', 'content_type')
    action_serializer_classes = {
        "retrieve": BarcTagSerializer,
        "create": CreateBarcTagSerializer,
        "update": CreateBarcTagSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(BarcTagViewSet, self).get_serializer_class()


class ProgramGenreViewSet(ModelViewSet):
    queryset = ProgramGenre.objects.all()
    serializer_class = DetailProgramGenreSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code", "program_theme__name")
    search_fields = ('name', "code")
    action_serializer_classes = {
        "retrieve": DetailProgramGenreSerializer,
        "create": ProgramGenreSerializer,
        "update": ProgramGenreSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(ProgramGenreViewSet, self).get_serializer_class()

    def list(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("name", search.replace("+"," ").strip())
        program_theme = request.query_params.get("program_theme", search)
        created_on = request.query_params.get("created_on", None)
        page = int(request.query_params.get("page", 1))
        qs = ProgramGenre.objects.all()
        if title and not title.isdigit():
            qs = qs.filter(name__istartswith=title)
        if title and title.isdigit():
            qs = qs.filter(code__istartswith=title)
        if program_theme and not program_theme.isdigit():
            qs = qs.filter(program_theme__name__istartswith=title)
        if program_theme and program_theme.isdigit():
            qs = qs.filter(program_theme__code__istartswith=title)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        qs = qs.order_by("name")
        ser = DetailProgramGenreSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        # ser_data = []
        # for qd in ser.data:
        #     if not qd['name'].isdigit():
        #         ser_data.append(qd)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size})


class ProgramThemeViewSet(ModelViewSet):
    queryset = ProgramTheme.objects.all()
    serializer_class = ProgramThemeSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code")
    search_fields = ('name', "code")


class AdvertiserGroupViewSet(ModelViewSet):
    queryset = AdvertiserGroup.objects.all()
    serializer_class = AdvertiserGroupSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code")
    search_fields = ('name', "code")


class AdvertiserViewSet(ModelViewSet):
    queryset = Advertiser.objects.all()
    serializer_class = DetailAdvertiserSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code", 'advertiser_group__name', 'advertiser_group')
    search_fields = ('name', "code")
    action_serializer_classes = {
        "retrieve": DetailAdvertiserSerializer,
        "create": AdvertiserSerializer,
        "update": AdvertiserSerializer
    }

    def get_queryset(self):
        n = self.request.query_params.get("type",None)
        if n :
            if n =="commercial":
                return self.queryset.filter(commercial__isnull=False).distinct()
            elif n =="promo":
                return self.queryset.filter(promo__isnull=False).distinct()
            else:
                return self.queryset
        return self.queryset

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(AdvertiserViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        id = serializer.data['id']
        p = Advertiser.objects.get(id=id)
        ser = DetailAdvertiserSerializer(p)
        return Response(ser.data, status=status.HTTP_201_CREATED, headers=headers)


class BrandCategoryViewSet(ModelViewSet):
    queryset = BrandCategory.objects.all()
    serializer_class = DetailBrandCategorySerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code", "brand_sector", "brand_sector__name")
    search_fields = ('name', "code")
    action_serializer_classes = {
        "retrieve": DetailBrandCategorySerializer,
        "create": BrandCategorySerializer,
        "update": BrandCategorySerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(BrandCategoryViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        id = serializer.data['id']
        p = BrandCategory.objects.get(id=id)
        ser = DetailBrandCategorySerializer(p)
        return Response(ser.data, status=status.HTTP_201_CREATED, headers=headers)


class BrandSectorViewSet(ModelViewSet):
    queryset = BrandSector.objects.all()
    serializer_class = BrandSectorSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code")
    search_fields = ('name', "code")
    action_serializer_classes = {
        "retrieve": BrandSectorSerializer,
        "create": CreateBrandSectorSerializer,
        "update": CreateBrandSectorSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(BrandSectorViewSet, self).get_serializer_class()


class BrandNameViewSet(LoggingMixin, ModelViewSet):
    queryset = BrandName.objects.all()
    serializer_class = DetailBrandNameSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code", "brand_category", "brand_category__name", "brand_category__brand_sector__name")
    search_fields = ('name', "code")
    action_serializer_classes = {
        "retrieve": DetailBrandNameSerializer,
        "create": BrandNameSerializer,
        "update": BrandNameSerializer
    }

    def get_queryset(self):
        n = self.request.query_params.get("type",None)
        if n :
            if n =="commercial":
                return self.queryset.filter(commercial__isnull=False).distinct()
            elif n =="promo":
                return self.queryset.filter(promo__isnull=False).distinct()
            else:
                return self.queryset
        return self.queryset


    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(BrandNameViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        id = serializer.data['id']
        p = BrandName.objects.get(id=id)
        ser = DetailBrandNameSerializer(p)
        return Response(ser.data, status=status.HTTP_201_CREATED, headers=headers)


class TitleViewSet(LoggingMixin, ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code")
    search_fields = ('name', "code")
    action_serializer_classes = {
        "retrieve": TitleSerializer,
        "create": CreateTitleSerializer,
        "update": CreateTitleSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(TitleViewSet, self).get_serializer_class()


class SpecChannelViewSet(ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code")
    search_fields = ('name', "code")

    def list(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("name", search.replace("+"," ").strip())
        created_on = request.query_params.get("created_on", None)
        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if title and not title.isdigit():
            qs = qs.filter(name__istartswith=title)
        if title and title.isdigit():
            qs = qs.filter(code__istartswith=title)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        qs = qs.order_by("name")
        ser = ChannelSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size})


class ChannelGenreViewSet(ModelViewSet):
    queryset = ChannelGenre.objects.all()
    serializer_class = ChannelGenreSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code")
    search_fields = ('name', "code")


class ChannelNetworkViewSet(ModelViewSet):
    queryset = ChannelNetwork.objects.all()
    serializer_class = ChannelNetworkSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code")
    search_fields = ('name', "code")


class RegionViewSet(ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code")
    search_fields = ('name', "code")


class ContentLanguageViewSet(ModelViewSet):
    queryset = ContentLanguage.objects.all()
    serializer_class = ContentLanguageSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("name", "code")
    search_fields = ('name', "code")

    def list(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("name", search.replace("+"," ").strip())
        created_on = request.query_params.get("created_on", None)
        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if title and not title.isdigit():
            qs = qs.filter(name__istartswith=title)
        if title and title.isdigit():
            qs = qs.filter(code__istartswith=title)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        qs = qs.order_by("name")
        ser = ContentLanguageSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size})


class ProductionHouseViewSet(ModelViewSet):
    queryset = ProductionHouse.objects.all()
    serializer_class = ProductionHouseSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("title", "code")
    search_fields = ('title', "code")


class ProgramViewSet(LoggingMixin, ModelViewSet):
    queryset = Program.objects.filter(channel__isnull=False).order_by('title__name')
    serializer_class = DetailProgramSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # filter_class = ProgramFilter
    search_fields = ('title__name',)
    action_serializer_classes = {
        "retrieve": DetailProgramSerializer,
        "create": ProgramSerializer,
        "update": ProgramSerializer
    }

    # def get_queryset(self):
    #     """
    #     This view should return a list of all models by
    #     the maker passed in the URL
    #     """
    #     search = self.request.query_params.get('search', None)
    #     channel_code = self.request.query_params.get('channel_code', None)
    #     qs = None
    #     if search and channel_code:
    #         qs1 = Program.objects.filter(Q(title__name__iexact=search)& Q(channel__code=channel_code))
    #         qs2 = Program.objects.filter(Q(title__name__icontains=search)& Q(channel__code=channel_code))
    #         program_tags = list(chain(qs1,qs2))
    #         qs = program_tags
    #     elif search:
    #         qs = Program.objects.all().filter(Q(title__name__icontains=search))
    #     elif channel_code:
    #         qs = Program.objects.all().filter(Q(channel__code=channel_code))
    #     else:
    #         qs = Program.objects.all()
    #     return qs

    def list(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", search)
        language = request.query_params.get("language", "")
        channel = request.query_params.get("channel", "")
        program_theme = request.query_params.get("program_theme", "")
        program_genre = request.query_params.get("program_genre", "")
        created_on = request.query_params.get("created_on", None)

        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if title:
            qs = qs.filter(title__name__istartswith=title)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        if program_genre:
            qs = qs.filter(program_genre__name__istartswith=program_genre)
        if program_theme:
            qs = qs.filter(program_genre__program_theme__name__istartswith=program_theme)
        if language:
            qs = qs.filter(language__name__istartswith=language)
        if channel and not channel.isdigit():
            qs = qs.filter(channel__name__istartswith=channel)
        elif channel and channel.isdigit():
            qs = qs.filter(channel__code__istartswith=channel)
        qs = qs.order_by("title__name")
        ser = DetailProgramSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size})

    @detail_route(methods=['get'])
    def logs(self, request, pk=None):
        comm = self.get_object()
        ids = [str(comm.id)]
        v_ids = [str(x.id) for x in comm.vendorprogram_set.all()]
        ids += v_ids
        f = [Q(path__contains=str(id)) | Q(query_params__contains=str(id)) for id in ids]
        if f:
            filter_query = f[0]
            for filter_cn in f:
                filter_query |= filter_cn
            b = APIRequestLog.objects.filter(filter_query)
        else:
            b = None
        data = []
        for blog in b:
            action = ""
            if "accept" in blog.path.lower():
                action = "Accept"
            if "merge" in blog.path.lower():
                action = "Merge"
            if str(comm.id) in blog.path.lower():
                action = "Edit"
            if action:
                data.append(
                    {
                        'user': blog.user.first_name,
                        'query_params': blog.query_params,
                        'action': action,
                        'time': blog.requested_at,
                        'id': ''
                    }
                )
        return Response(data=data)

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(ProgramViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        id = serializer.data['id']
        p = Program.objects.get(id=id)
        ser = DetailProgramSerializer(p)
        return Response(ser.data, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['post'])
    def mark_review(self, request):
        emails = request.data.get("emails", '')
        body = request.data.get("body", "")
        subject = request.data.get("subject", '')
        t = unquote(body)
        send_mail(subject,
                  body, "support@tessact.com",
                  emails.split(','), html_message=t)
        return Response(status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def multi_merge(self, request, pk=None):
        ids = request.query_params.get("ids", "")
        if ids:
            qs = self.queryset.filter(id__in=ids.split(","))
            vc = self.queryset.filter(id=ids.split(",")[0]).first()
            qs_left = qs.exclude(id=ids.split(",")[0])
            qs_left.update(deleted=True)
            vc_objs = VendorProgram.objects.filter(program__id__in=ids.split(","))
            vc_objs.update(program=vc)
            return response.Response(data={"id": vc.id}, status=status.HTTP_200_OK)
        else:
            return response.Response(status=status.HTTP_400_BAD_REQUEST)


class PromoViewSet(LoggingMixin, ModelViewSet):
    queryset = Promo.objects.all().order_by('brand_name__name')
    serializer_class = DetailPromoSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend)
    # filter_class = PromoFilter
    search_fields = ('brand_name__name',)
    action_serializer_classes = {
        "retrieve": DetailPromoSerializer,
        "create": PromoSerializer,
        "update": PromoSerializer
    }

    @list_route(methods=['post'])
    def mark_review(self, request):
        emails = request.data.get("emails", '')
        body = request.data.get("body", "")
        subject = request.data.get("subject", '')
        t = unquote(body)
        send_mail(subject,
                  body, "support@tessact.com",
                  emails.split(','), html_message=t)
        return Response(status=status.HTTP_200_OK)
        # return Response(status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", search)
        brand_sector = request.query_params.get("brand_sector", "")
        brand_category = request.query_params.get("brand_category", "")
        advertiser = request.query_params.get("advertiser","")
        advertiser_group = request.query_params.get("advertiser_group","")
        descriptor = request.query_params.get("descriptor","")
        created_on = request.query_params.get("created_on", None)
        has_video = request.query_params.get("has_video", None)

        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if title:
            qs = qs.filter(brand_name__name__istartswith=title)
        if brand_sector:
            qs = qs.filter(brand_name__brand_category__brand_sector__name__istartswith=brand_sector)
        if brand_category:
            qs = qs.filter(brand_name__brand_category__name__istartswith=brand_category)
        if advertiser:
            qs = qs.filter(advertiser__name__istartswith=advertiser)
        if advertiser_group:
            qs = qs.filter(advertiser__advertiser_group__name__istartswith=advertiser_group)
        if descriptor:
            qs = qs.filter(descriptor__text__icontains=descriptor)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        if has_video:
            ids = VendorPromo.objects.all().filter(promo__isnull=False, video__isnull=False).values_list("promo", flat=True)
            ids = [str(x) for x in ids]
            qs = qs.filter(id__in=ids)
        qs = qs.order_by("brand_name__name")
        ser = DetailPromoSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size})

    @detail_route(methods=['get'])
    def logs(self, request, pk=None):
        comm = self.get_object()
        ids = [str(comm.id)]
        v_ids = [str(x.id) for x in comm.vendorpromo_set.all()]
        ids += v_ids
        f = [Q(path__contains=str(id)) | Q(query_params__contains=str(id)) for id in ids]
        if f:
            filter_query = f[0]
            for filter_cn in f:
                filter_query |= filter_cn
            b = APIRequestLog.objects.filter(filter_query)
        else:
            b = None
        data = []
        for blog in b:
            action = ""
            if "accept" in blog.path.lower():
                action = "Accept"
            if "merge" in blog.path.lower():
                action = "Merge"
            if action:
                data.append(
                    {
                        'user': blog.user.first_name,
                        'query_params': blog.query_params,
                        'action': action,
                        'time': blog.requested_at,
                        'id': ''
                    }
                )
        return Response(data=data)
    # def get_queryset(self):
    #     """
    #     This view should return a list of all models by
    #     the maker passed in the URL
    #     """
    #     search = self.request.query_params.get('search', None)
    #
    #     if search :
    #
    #         qs1 = Promo.objects.filter(Q(brand_name__name__iexact=search)|Q(title__name__iexact=search))
    #         qs2 = Promo.objects.filter(Q(brand_name__name__icontains=search))
    #         promo_tags = list(chain(qs1,qs2))
    #         return promo_tags
    #     else:
    #         return Promo.objects.all()

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(PromoViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        id = serializer.data['id']
        p = Promo.objects.get(id=id)
        ser = DetailPromoSerializer(p)
        return Response(ser.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['get'])
    def report_events(self, request, pk=None):
        vcr = VendorReportPromo.objects.filter(promo__promo=self.get_object()).values("channel__name", "duration"). \
            order_by("channel__name", "duration").annotate(Count("id"))
        ser = VendorReportCountSerializer(vcr, many=True)
        return response.Response(data=ser.data)

    @list_route(methods=['get'])
    def multi_merge(self, request, pk=None):
        ids = request.query_params.get("ids", "")
        if ids:
            qs = self.queryset.filter(id__in=ids.split(","))
            vc = self.queryset.filter(id=ids.split(",")[0]).first()
            qs_left = qs.exclude(id=ids.split(",")[0])
            qs_left.update(deleted=True)
            vc_objs = VendorPromo.objects.filter(promo__id__in=ids.split(","))
            vc_objs.update(promo=vc)
            return response.Response(data={"id": vc.id}, status=status.HTTP_200_OK)
        else:
            return response.Response(status=status.HTTP_400_BAD_REQUEST)


class CommercialViewSet(LoggingMixin, ModelViewSet):
    queryset = Commercial.objects.all().order_by('brand_name__name')
    serializer_class = DetailCommercialSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = CommercialFilter
    search_fields = ('title__name',)
    action_serializer_classes = {
        "retrieve": DetailCommercialSerializer,
        "create": CommercialSerializer,
        "update": CommercialSerializer
    }

    @list_route(methods=['get'])
    def mark_review(self, request):
        emails = request.data.get("emails", '')
        body = request.data.get("body", "")
        subject = request.data.get("subject", '')
        t = unquote(body)
        send_mail(subject,
                  body, "support@tessact.com",
                  emails.split(','), html_message=t)
        return Response(status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def logs(self,request, pk=None):
        comm = self.get_object()
        ids = [str(comm.id)]
        v_ids = [str(x.id) for x in comm.vendorcommercial_set.all()]
        ids += v_ids
        f = [Q(path__contains=str(id))|Q(query_params__contains=str(id)) for id in ids]
        if f:
            filter_query = f[0]
            for filter_cn in f:
                filter_query |= filter_cn
            b = APIRequestLog.objects.filter(filter_query)
        else:
            b = None
        data = []
        for blog in b:
            action = ""
            if "accept" in blog.path.lower() :
                action="Accept"
            if "merge" in blog.path.lower() :
                action="Merge"
            if action:
                data.append(
                    {
                        'user': blog.user.first_name,
                        'query_params': blog.query_params,
                        'action': action,
                        'time': blog.requested_at,
                        'id': ''
                    }
                )
        return Response(data=data)
    # def get_queryset(self):
    #     """
    #     This view should return a list of all models by
    #     the maker passed in the URL
    #     """
    #     # search = self.request.query_params.get('search', None)
    #     video = self.request.query_params.get('has_video', None)
    #     # qs = None
    #     # if search :
    #     #     qs1 = Commercial.objects.filter(Q(title__name__iexact=search))
    #     #     qs2 = Commercial.objects.filter(Q(title__name__icontains=search))
    #     #     commercial_tags = list(chain(qs1,qs2))
    #     #     qs = commercial_tags
    #     # else:
    #     qs = Commercial.objects.all()
    #
    #     if video:
    #         d_text = []
    #         bd_text = []
    #         for t in CommercialTag.objects.all():
    #             d_text.append(t.descriptor)
    #             bd_text.append(t.brand_title)
    #         qs = qs.filter(descriptor__text__in=d_text, brand_name__name__in=bd_text)
    #     return qs

    def list(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", search)
        brand_sector = request.query_params.get("brand_sector", "")
        brand_category = request.query_params.get("brand_category", "")
        advertiser = request.query_params.get("advertiser","")
        advertiser_group = request.query_params.get("advertiser_group","")
        descriptor = request.query_params.get("descriptor","")
        created_on = request.query_params.get("created_on", None)
        has_video = request.query_params.get("has_video", False)
        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if title and not title.isdigit():
            qs = qs.filter(brand_name__name__istartswith=title)
        if title and title.isdigit():
            qs = qs.filter(brand_name__code__istartswith=title)
        if brand_sector:
            qs = qs.filter(brand_name__brand_category__brand_sector__name__istartswith=brand_sector)
        if brand_category:
            qs = qs.filter(brand_name__brand_category__name__istartswith=brand_category)
        if advertiser and not advertiser.isdigit():
            qs = qs.filter(advertiser__name__istartswith=advertiser)
        if advertiser and advertiser.isdigit():
            qs = qs.filter(advertiser__code__istartswith=advertiser)
        if advertiser_group:
            qs = qs.filter(advertiser__advertiser_group__name__istartswith=advertiser_group)
        if descriptor and not descriptor.isdigit():
            qs = qs.filter(descriptor__text__icontains=descriptor)
        if descriptor and descriptor.isdigit():
            qs = qs.filter(descriptor__code__icontains=descriptor)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        if has_video:
            ids = VendorCommercial.objects.all().filter(commercial__isnull=False, video__isnull=False).values_list("commercial", flat=True)
            ids = [str(x) for x in ids]
            qs = qs.filter(id__in=ids)
        qs = qs.order_by("brand_name__name")
        ser = DetailCommercialSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size})

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(CommercialViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        id = serializer.data['id']
        p = Commercial.objects.get(id=id)
        ser = DetailCommercialSerializer(p)
        return Response(ser.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['get'])
    def report_events(self, request, pk=None):
        vcr = VendorReportCommercial.objects.filter(commercial__commercial=self.get_object()).values("channel__name", "duration"). \
            order_by("channel__name", "duration").annotate(Count("id"))
        ser = VendorReportCountSerializer(vcr, many=True)
        return response.Response(data=ser.data)

    @list_route(methods=['get'])
    def multi_merge(self, request, pk=None):
        ids = request.query_params.get("ids", "")
        if ids:
            qs = self.queryset.filter(id__in=ids.split(","))
            vc = self.queryset.filter(id=ids.split(",")[0]).first()
            qs_left = qs.exclude(id=ids.split(",")[0])
            qs_left.update(deleted=True)
            vc_objs = VendorCommercial.objects.filter(commercial__id__in=ids.split(","))
            vc_objs.update(commercial=vc)
            return response.Response(data={"id": vc.id}, status=status.HTTP_200_OK)
        else:
            return response.Response(status=status.HTTP_400_BAD_REQUEST)


class TProgramViewSet(ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = TDetailProgramSerializer
    permission_classes = (permissions.IsAuthenticated, )
    # filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    # filter_class = ProgramFilter
    # search_fields = ('title__name', "title__code", "channel__name")
    action_serializer_classes = {
        "retrieve": TDetailProgramSerializer,
        "create": ProgramSerializer,
        "update": ProgramSerializer
    }

    def get_queryset(self):
        """
        This view should return a list of all models by
        the maker passed in the URL
        """
        search = self.request.query_params.get('search', None)
        channel_code = self.request.query_params.get('channel_code', None)
        if search and channel_code:
            qs1 = Program.objects.filter(Q(title__name__iexact=search)& Q(channel__code=channel_code))
            qs2 = Program.objects.filter(Q(title__name__icontains=search)& Q(channel__code=channel_code))
            program_tags = list(chain(qs1,qs2))
            return program_tags
        elif search:
            return Program.objects.all().filter(Q(title__name__icontains=search))
        elif channel_code:
            return Program.objects.all().filter(Q(channel__code=channel_code))
        else:
            return Program.objects.all()

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(TProgramViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        id = serializer.data['id']
        p = Program.objects.get(id=id)
        ser = DetailProgramSerializer(p)
        return Response(ser.data, status=status.HTTP_201_CREATED, headers=headers)


class TPromoViewSet(ModelViewSet):
    queryset = Promo.objects.all()
    serializer_class = TDetailPromoSerializer
    permission_classes = (permissions.IsAuthenticated, )
    # filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    # filter_class = PromoFilter
    # search_fields = ('brand_name__name', "brand_name__code")
    action_serializer_classes = {
        "retrieve": TDetailPromoSerializer,
        "create": PromoSerializer,
        "update": PromoSerializer
    }

    def get_queryset(self):
        """
        This view should return a list of all models by
        the maker passed in the URL
        """
        search = self.request.query_params.get('search', None)

        if search :
            qs1 = Promo.objects.filter(Q(brand_name__name__iexact=search))
            qs2 = Promo.objects.filter(Q(brand_name__name__icontains=search))
            promo_tags = list(chain(qs1,qs2))
            return promo_tags
        else:
            return Promo.objects.all()

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(TPromoViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        id = serializer.data['id']
        p = Promo.objects.get(id=id)
        ser = DetailPromoSerializer(p)
        return Response(ser.data, status=status.HTTP_201_CREATED, headers=headers)


class TCommercialViewSet(ModelViewSet):
    queryset = Commercial.objects.all()
    serializer_class = TDetailCommercialSerializer
    permission_classes = (permissions.IsAuthenticated, )
    # filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    # filter_class = CommercialFilter
    # search_fields = ('title__name', "title__code")
    action_serializer_classes = {
        "retrieve": TDetailCommercialSerializer,
        "create": CommercialSerializer,
        "update": CommercialSerializer
    }

    def get_queryset(self):
        """
        This view should return a list of all models by
        the maker passed in the URL
        """
        search = self.request.query_params.get('search', None)
        video = self.request.query_params.get('has_video', None)
        qs = None
        if search :
            qs1 = Commercial.objects.filter(Q(title__name__iexact=search))
            qs2 = Commercial.objects.filter(Q(title__name__icontains=search))
            commercial_tags = list(chain(qs1,qs2))
            qs = commercial_tags
        else:
            qs = Commercial.objects.all()

        if video:
            d_text = []
            bd_text = []
            for t in CommercialTag.objects.all():
                d_text.append(t.descriptor)
                bd_text.append(t.brand_title)
            qs = qs.filter(descriptor__text__in=d_text, brand_name__name__in=bd_text)
        return qs

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(TCommercialViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        id = serializer.data['id']
        p = Commercial.objects.get(id=id)
        ser = DetailCommercialSerializer(p)
        return Response(ser.data, status=status.HTTP_201_CREATED, headers=headers)


class DescriptorViewSet(ModelViewSet):
    queryset = Descriptor.objects.all()
    serializer_class = DescriptorSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("text",)
    search_fields = ('text',)
    action_serializer_classes = {
        "retrieve": DescriptorSerializer,
        "create": CreateDescriptorSerializer,
        "update": CreateDescriptorSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(DescriptorViewSet, self).get_serializer_class()

    def get_queryset(self):
        n = self.request.query_params.get("type",None)
        if n :
            if n =="commercial":
                return self.queryset.filter(commercial__isnull=False).distinct()
            elif n =="promo":
                return self.queryset.filter(promo__isnull=False).distinct()
            else:
                return self.queryset
        return self.queryset


class PlayoutTagViewSet(ModelViewSet):
    queryset = PlayoutTag.objects.all().order_by('video', 'frame_in')
    serializer_class = PlayoutTagSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = StandardResultsSetPagination
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('video', 'content_type')
    action_serializer_classes = {
        "retrieve": PlayoutTagSerializer,
        "create": CreatePlayoutTagSerializer,
        "update": CreatePlayoutTagSerializer
    }

    def get_queryset(self):
        """
        This view should return a list of all models by
        the maker passed in the URL
        """
        channel = self.request.query_params.get('channel', None)
        dt = self.request.query_params.get('date', None)
        if channel and dt:
            # channel_clips = ChannelClip.objects.filter(Q(channel=ch_obj) and Q(date=date)).values_list('video__id', flat=True)
            playout_tags = PlayoutTag.objects.filter(Q(video__channelclip__channel__id=channel)and Q(video__channelclip__date=dt)).order_by('video__channelclip__start_time', 'frame_in')
            return playout_tags
        else:
            return PlayoutTag.objects.all().order_by('video', 'frame_in')

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(PlayoutTagViewSet, self).get_serializer_class()

    @list_route(methods=['get'])
    def get_mct(self, request):
        start_date = request.query_params.get("start_date",None)
        end_date = request.query_params.get("end_date",None)

        if end_date and start_date:
            send_mct.delay('aswin@tessact.com', start_date,end_date)

        return response.Response(status=status.HTTP_200_OK)


class SpriteTagViewSet(ModelViewSet):
    queryset = SpriteTag.objects.all().order_by('time')
    serializer_class = SpriteTagSerializer
    pagination_class = ShortResultsSetPagination
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("video", "time")
    search_fields = ("video__title",)

    @list_route(methods=['get'])
    def create_sprites(self, request):
        vid = request.query_params.get('vid', None)
        start = request.query_params.get('start', 0)
        end = request.query_params.get('end', 59)
        #time = request.query_params.get('time', None) 
        channel = request.query_params.get('channel', None)
        bucket = request.query_params.get('bucket', None)

        if not bucket:
            base_url = "https://s3.ap-south-1.amazonaws.com/trigger-uploaded-videos/{}/{}/sprite{}.png"
            v = Video.objects.filter(id=vid).first()
            if base_url and v and channel and vid:
                for i in range(int(start), int(end)):
                    s, created = SpriteTag.objects.get_or_create(video=v, time=i, url=base_url.format(channel, vid, i))
        else:
            base_url = "https://s3.ap-south-1.amazonaws.com/{}/sprites/{}/{}/sprite{}.png"
            v = Video.objects.filter(id=vid).first()
            if base_url and v and channel and vid:
                for i in range(int(start), int(end)):
                    s, created = SpriteTag.objects.get_or_create(video=v, time=i, url=base_url.format(bucket, channel, vid, i))
        return Response(data={"response": "success"}, status=status.HTTP_404_NOT_FOUND)


class CommercialTagViewSet(ModelViewSet):
    queryset = CommercialTag.objects.all()
    serializer_class = CommercialTagSerializer
    permission_classes = (permissions.IsAuthenticated, )

class GenericTagViewSet(ModelViewSet):
    """
    Creating a Viewset for Content Type
    """
    serializer_class = DetailGenericTagSerializer
    queryset = GenericTag.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,)
    search_fields = ("title",)
    filter_class = GenericTagFilter #filter_fields=("level", "parent")

    action_serializer_classes = {
        "retrieve": DetailGenericTagSerializer,
        "create": GenericTagSerializer,
        "update": GenericTagSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(GenericTagViewSet, self).get_serializer_class()

class ManualTagQCStatusViewSet(ModelViewSet):
    queryset = ManualTagQCStatus.objects.all()
    serializer_class = ManualTagQCStatusSerializer
    permission_classes = (permissions.IsAuthenticated, )

    @list_route(methods=['post'])
    def change_status(self, request):
        data = request.data
        objs = ManualTagQCStatus.objects.filter(tag__id=data['tag'], manual_tag__id=data['manual_tag'])

        if objs:
            if objs.count()==1:
                manual_tag_qc = objs.first()
                manual_tag_qc.qc_approved=data['qc_approved']
                manual_tag_qc.save()
                ser = ManualTagQCStatusSerializer(manual_tag_qc)
                return Response(data=ser.data, status=status.HTTP_201_CREATED)
            else:
                return Response(data={"response":"failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(data={"response":"failed"}, status=status.HTTP_400_BAD_REQUEST)


class MarkerViewSet(ModelViewSet):
    """
    Creating a Viewset for Content Type
    """
    serializer_class = MarkerSerializer
    queryset = Marker.objects.all()
    permission_classes = (IsAuthenticated,)

    
    action_serializer_classes = {
        "retrieve": MarkerSerializer,
        "create": MarkerSerializer,
        "update": MarkerSerializer,
        "list": MarkerSerializer
    }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(MarkerViewSet, self).get_serializer_class()