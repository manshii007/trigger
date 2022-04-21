#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from rest_framework import viewsets, filters, reverse
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status, mixins
from rest_framework.parsers import JSONParser
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.db.models import Count, Func, query
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import get_objects_for_user, get_objects_for_group, assign_perm, ObjectPermissionChecker
from itertools import groupby, chain
from video.tasks import sec2tcr, advanced_search
from django.db.models import Q, F
from users.models import User
import operator
import re
from functools import reduce
import urllib.parse
import boto3
from botocore.exceptions import ClientError
import csv

import random
import math
from .tasks import send_report
import django_filters
from .pagination import CustomPagination, ShortResultsSetPagination
from .serializers import (
    # GenericLibrarySerializer,
    CreateProjectVersionSerializer,
    DetailedProjectFileSerializer,
    DetailedProjectMetadataSerializer,
    DetailedProjectSerializer,
    DetailedSearchAssetVersionSerializer,
    PersonSerializer,
    FileSerializer,
    NewFileSerializer,
    NewFolderSerializer,
    ContentsSerializer,
    FolderSerializer,
    FolderSearchSerializer,
    DetailSongSerializer,
    DetailSeriesSerializer,
    CharacterSerializer,
    ChannelSerializer,
    GenreSerializer,
    EpisodeSerializer,
    ProjectFileSerializer,
    ProjectMetadataSerializer,
    ProjectSerializer,
    ProjectVersionSerializer,
    SeriesSerializer,
    ContextTypeSerializer,
    PoliticianSerializer,
    DetailPersonSerializer,
    CreatePoliticianSerializer,
    PoliticiansByDate,
    PoliticiansByDateUser,
    PoliticiansByUser,
    ActorSerializer,
    TVAnchorSerializer,
    CreateTVAnchorSerializer,
    MovieSegmentSerializer,
    MovieSerializer,
    EpisodeSegmentSerializer,
    CreateEpisodeSegmentSerializer,
    CreateEpisodeSerializer,
    CreateMovieSerializer,
    CreateMovieSegmentSerializer,
    CreatePersonSerializer,
    TriviaSerializer,
    CreateTriviaSerializer,
    DetailActorSerializer,
    PersonGroupSerializer,
    CreatePersonGroupSerializer,
    LoadTriviaSerializer,
    UpdateTriviaSerializer,
    PlaylistEntrySerializer,
    PlaylistSerializer,
    SongSerializer,
    TriviaLogSerializer,
    LabelSerializer,
    DetailPlaylistSerializer,
    NxSongSerializer,
    LoadMovieTriviaSerializer,
    DetailTriviaSerializer,
    NxMovieSerializer,
    CreateTriviaLogSerializer,
    TriviaEditLogSerializer,
    TriviaReviewLogSerializer,
    LoadGenericTriviaSerializer,
    CreateChannelClipSerializer,
    ChannelClipSerializer,
    BarcChannelSerializer,
    PromoSegmentSerializer,
    PromoSerializer,
    DetailedPromoSerializer,
    SongVerificationSerializer,
    AssetVersionSerializer,
    DetailedAssetVersionSerializer,
    CollectionSerializer,
    DetailedCollectionSerializer,
    AssignWorkFlowInstanceStepSerializer,
    SegmentSerializer,
    RushesSerializer,
    DetailedRushesSerializer,
    ContentTypeSerializer,
    MetadataAudioSerializer,
    SongAssetSerializer,
    DetailedSongAssetSerializer,
    BatchSerializer,
    VideoProcessingStatusSerializer,
    SequenceSerializer,
    SeasonSerializer,
    DetailedSeriesSerializer,
    CreateSeasonSerializer,
    WorkFlowMetadataSerializer,
    WorkFlowSerializer,
    DetailedWorkFlowSerializer,
    WorkFlowStepSerializer,
    WorkFlowInstanceSerializer,
    WorkFlowInstanceStepSerializer,
    DetailedWorkFlowInstanceSerializer,
    WorkFlowStageSerializer,
    WorkFlowTransitionHistorySerializer,
    PromoTitleSerializer,
    CognitiveSearchPromoSerializer,
    CognitiveSearchRushesSerializer,
    CognitiveSearchSeriesSerializer,
    CognitiveSearchSeasonSerializer,
    CognitiveSearchEpisodeSerializer,
    CommercialAssetSerializer,
    DetailedCommercialAssetSerializer,
    DetailedWorkFlowStageSerializer,
    WorkFlowCollectionInstanceSerializer,
    AssignWorkFlowCollectionInstanceStepSerializer,
    WorkFlowCollectionInstanceStepSerializer,
    DetailedWorkFlowCollectionInstanceSerializer,
    CognitiveSearchSongAssetSerializer,
    CognitiveSearchMovieSerializer,
    CognitiveSearchCommercialAssetSerializer,
    DemoSerializer,
    CreateSeriesSerializer,
    NewCategoriesSerializer,
    CategoriesSerializer
)
from .models import (
    ProjectFiles,
    ProjectMetadata,
    ProjectVersion,
    Projects,
    TVAnchor,
    Person,
    Character,
    Channel,
    Genre,
    Episode,
    Series,
    ContextType,
    Politician,
    EpisodeSegment,
    MovieSegment,
    Movie,
    Trivia,
    Actor,
    PersonGroup,
    CloudPerson,
    Song,
    TriviaLog,
    PlaylistEntry,
    Playlist,
    Label,
    NxSong,
    TriviaEditLog,
    TriviaReviewLog,
    ChannelClip,
    Promo,
    PromoSegment,
    SongVerification,
    AssetVersion,
    Collection,
    AssignWorkFlowInstanceStep,
    Segment,
    Rushes,
    MetadataAudio,
    SongAsset,
    Batch,
    VideoProcessingStatus,
    Sequence,
    Season,
    WorkFlow,
    WorkFlowMetadata,
    WorkFlowStep,
    WorkFlowInstance,
    WorkFlowInstanceStep,
    WorkFlowStage,
    WorkFlowTransitionHistory,
    CommercialAsset,
    WorkFlowCollectionInstance,
    WorkFlowCollectionInstanceStep,
    AssignWorkFlowCollectionInstanceStep,
    Demo,
    DemoOTP,
    Folder,
    File
)
from .filters import (
    PersonFilter,
    CharacterFilter,
    GenreFilter,
    EpisodeFilter,
    ProjectFilter,
    SeriesFilter,
    ContextTypeFilter,
    ChannelFilter,
    PoliticianFilter,
    TVAnchorFilter,
    MovieFilter,
    TriviaFilter,
    TriviaEditLogFilter,
    PromoFilter,
    SeasonFilter,
    RushesFilter,
)
from tags.models import Channel as SpecChannel
from video.models import Video
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework.decorators import detail_route, list_route, api_view, parser_classes, permission_classes, authentication_classes
import logging
import sys
from .app import InstagramScraper
from .tasks import put_fingerprint
from workgroups.models import WorkGroupMembership, Permission, Role, WorkGroup, Team, Group
from permissions.permissions import CustomObjectPermission, CustomDjangoModelPermission, CustomDjangoContentPermission, ContentChannelControlMixin, UserAccessModelPermission
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import models

from users.serializers import CreateUserSerializer, UserSerializer
from pagination.pagination import StandardResultsSetPagination


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

# create custom sql function


class ExtractDateFunction(Func):
    function = "DATE"


def filter_content_by_channel(queryset, request):
    user_all_memberships = WorkGroupMembership.objects.filter(
        user=request.user)
    user_all_roles = Role.objects.filter(
        workgroupmembership__in=user_all_memberships)
    user_all_perms = list(Permission.objects.filter(
        role__in=user_all_roles).values_list("codename", flat=True))
    channels = Channel.objects.all()
    channel_perms = ["can_access_{}".format(
        channel.channel_name.lower().replace(" ", "_")) for channel in channels]
    allowed_channel_perms = list(
        filter(lambda x: x in user_all_perms, channel_perms))
    allowed_channels = [x.replace("can_access_", "").replace(
        "_", " ") for x in allowed_channel_perms]
    if allowed_channels and not request.user.is_superuser:
        query = reduce(operator.or_, (Q(channel__channel_name__iexact=x)
                                      for x in allowed_channels))
        queryset = queryset.filter(query)
    elif not request.user.is_superuser:
        queryset = queryset.filter(pk__isnull=True)
    return queryset


class InstaViewSet(viewsets.ViewSet):

    def list(self, request):
        id = request.query_params.get("id", None)
        end_cursor = request.query_params.get("end_cursor", '')
        name = request.query_params.get("name", 'iamsrk')
        args = {'usernames': [name],
                'login_user': "aswincsekar",
                'login_pass': 'JackAndJill1',
                'quiet': True,
                'maximum': 1000,
                'retain_username': False,
                'media_metadata': False,
                'media_types': ['image', 'video'],
                'latest': False
                }

        scrapper = InstagramScraper(**args)
        scrapper.login()
        nodes, end_cursor = scrapper.query_media(id, end_cursor)
        scrapper.quit = True
        scrapper.logout()
        return Response(data={"end_cursor": end_cursor, "id": id, "nodes": nodes}, status=status.HTTP_200_OK)


class NxSongViewSet(viewsets.ModelViewSet):
    serializer_class = NxSongSerializer
    queryset = NxSong.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend,)
    search_fields = ("content_id", "title")

    @list_route(methods=['get'])
    def get_trivia(self, request, **kwargs):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        logging.info(ip)
        print("IP : {}".format(ip))
        dummy = request.query_params.get("dummy", False)
        if dummy:
            logging.info("Dummy request >>>>>>>>>>>")
            id = request.query_params.get("content_id", None)
            logging.info(id)
            n = NxSong.objects.filter(content_id=id).first()

            if n:
                actors = n.actors.all()
                singers = n.singers.all()
                music_directors = n.music_directors.all()
                song_writers = n.song_writers.all()
                producers = n.producers.all()
                movie = n.movie
                key_persons = list(
                    chain(actors, singers, music_directors, song_writers, producers))
                f = [Q(persons__name=a.name) for a in key_persons]
                condition = None
                if f:
                    condition = reduce(operator.or_, f)

                if movie and condition:
                    condition = condition | Q(movie=movie)
                elif movie:
                    condition = Q(movie=movie)

                if condition:
                    trivias = Trivia.objects.filter(
                        Q(edit_status='ACP') & condition)
                else:
                    return Response(data={"trivia": []}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                logging.info(trivias.count())
                if trivias.count():
                    t = list(trivias)
                    random.shuffle(t)
                    t_final = t[0:1]
                    data = []
                    for t_f in t_final:
                        txt = t_f.edit_request if t_f.edit_request else t_f.trivia
                        data.append(txt)
                    return Response(data={"trivia": data}, status=status.HTTP_200_OK)
                else:
                    return Response(data={"trivia": []}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            count = request.query_params.get("count", '5')
            count = int(count)
            current_time = request.query_params.get("current_time", None)
            if current_time:
                current_time = datetime.strptime(current_time, '%Y%m%dT%H%M%S')
            else:
                current_time = datetime.now()
            next_time = request.query_params.get("next_time", None)
            if next_time:
                next_time = datetime.strptime(next_time, '%Y%m%dT%H%M%S')
            else:
                next_time = datetime.now()

            id = request.query_params.get("content_id", None)
            n = NxSong.objects.filter(content_id=id).first()

            if n:
                # create playlist
                c = Channel.objects.get(channel_name="9X Jalwa")
                p, created = Playlist.objects.get_or_create(
                    channel=c, date=datetime.now().date())
                if created:
                    p.active = True
                    p.save()
                    for pl in Playlist.objects.filter(channel=c, date__lt=datetime.now().date(), active=True):
                        pl.active = False
                        pl.save()
                try:
                    # create playlist_entry
                    pl_entry = PlaylistEntry.objects.get(playlist=p,
                                                         start_time=current_time,
                                                         end_time=next_time)
                except ObjectDoesNotExist:
                    pl_entry = PlaylistEntry.objects.create(playlist=p, content_object=n,
                                                            start_time=current_time,
                                                            end_time=next_time)
                except MultipleObjectsReturned:
                    pl_entry = PlaylistEntry.objects.filter(playlist=p,
                                                            start_time=current_time,
                                                            end_time=next_time).first()

                pl_entry.save()
                actors = n.actors.all()
                movie = n.movie
                f = [Q(persons__name=a.name) for a in actors]
                condition = None
                if f:
                    condition = reduce(operator.or_, f)

                if movie and condition:
                    condition = condition | Q(movie=movie)
                elif movie:
                    condition = Q(movie=movie)

                if condition:
                    trivias = Trivia.objects.filter(
                        edit_status='ACP').filter(condition)
                else:
                    trivias = Trivia.objects.filter(Q(edit_status='ACP'))
                if trivias.count():
                    t = list(trivias)
                    random.shuffle(t)
                    t_final = t[0:count]
                    data = []
                    for t_f in t_final:
                        txt = t_f.edit_request if t_f.edit_request else t_f.trivia
                        data.append(txt)
                    t_log = TriviaLog.objects.create(playlist_entry=pl_entry, trivia=t_final[
                                                     0], timestamp=datetime.now())
                    t_log.save()
                    return Response(data={"trivia": data}, status=status.HTTP_200_OK)
                else:
                    return Response(data={"trivia": []}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PoliticianViewSet(viewsets.ModelViewSet):
    serializer_class = PoliticianSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Politician.objects.all().order_by('-created_on')
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = PoliticianFilter
    search_fields = ('person__name', 'political_party',
                     "constituency", "positions")
    action_serializer_classes = {
        "create": CreatePoliticianSerializer,
        "update": CreatePoliticianSerializer
    }

    def get_serializer_class(self):

        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(PoliticianViewSet, self).get_serializer_class()

    @list_route(methods=['get'])
    def stats(self, request):
        politicians_by_date = Politician.objects.all()\
            .annotate(date_created=ExtractDateFunction("created_on"))\
            .values('date_created').order_by('-date_created').annotate(created_count=Count('id'))[:6]
        politicians_by_date_user = Politician.objects.all()\
            .annotate(date_created=ExtractDateFunction("created_on")) \
            .values('date_created', 'created_by').order_by('-date_created', 'created_by')\
            .annotate(created_count=Count('id'))
        politicians_by_user = list()
        for k, v in groupby(politicians_by_date_user.all(), lambda x: x['date_created']):
            tmp = dict()
            tmp['date'] = k
            tmp['data_list'] = list(v)
            politicians_by_user.append(tmp)
        serializer_for_user = PoliticiansByDateUser(
            politicians_by_user, many=True)
        serializer = PoliticiansByDate(politicians_by_date, many=True)
        politicians_by_date_for_month = Politician.objects.all().annotate(date_created=ExtractDateFunction(
            "created_on")).values('date_created').annotate(created_count=Count('id')).order_by('-date_created')[:27]
        serializer_for_month = PoliticiansByDate(
            politicians_by_date_for_month, many=True)
        return Response(data={
            "last_week": serializer.data,
            "last_month": serializer_for_month.data,
            "by_user": serializer_for_user.data,
            "total_entries": Politician.objects.all().count()
        }, status=status.HTTP_200_OK)


class PersonViewSet(viewsets.ModelViewSet):
    serializer_class = DetailPersonSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Person.objects.all().order_by('-created_on')
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    # filter_class = PersonFilter
    search_fields = ("name", "occupation", "id")
    action_serializer_classes = {
        "create": CreatePersonSerializer,
        "update": CreatePersonSerializer,
        "retrieve": DetailPersonSerializer,
    }
    ordering_fields = ('name',)

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(PersonViewSet, self).get_serializer_class()

    def list(self, request):
        """To accomodate created_on on date"""
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", None)
        created_on = request.query_params.get("created_on", None)
        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        if search:
            qs = qs.filter(name__icontains=search)
        qs = qs.order_by('-created_on')
        ser = DetailPersonSerializer(
            qs[(page - 1) * page_size:page * page_size], many=True, context={'request': request})

        count = qs.count()
        total_pages = math.ceil(count / page_size)

        return Response(data={"count": count, "page": page, "total_pages": total_pages,
                              "page_size": page_size, "results": ser.data})


class NxPersonViewSet(viewsets.ModelViewSet):
    serializer_class = DetailPersonSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Person.objects.filter(trivia__isnull=False).distinct().\
        annotate(pending_trivia=models.Sum(models.Case(models.When(trivia__is_approved='false', then=1), default=0,
                                                       output_field=models.IntegerField()))).order_by('-pending_trivia')
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    filter_class = PersonFilter
    search_fields = ("name", "occupation")
    action_serializer_classes = {
        "create": CreatePersonSerializer,
        "update": CreatePersonSerializer,
        "retrieve": DetailPersonSerializer,
    }
    ordering_fields = ('name',)

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(NxPersonViewSet, self).get_serializer_class()


class CharacterViewSet(viewsets.ModelViewSet):
    serializer_class = CharacterSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Character.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    filter_class = CharacterFilter
    search_fields = ("actor__name",)


class GenreViewSet(viewsets.ModelViewSet):
    serializer_class = GenreSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Genre.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    filter_class = GenreFilter
    search_fields = ("title",)


class EpisodeViewSet(viewsets.ModelViewSet):
    serializer_class = EpisodeSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Episode.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    filter_class = EpisodeFilter
    search_fields = ("title",)

    action_serializer_classes = {
        "create": CreateEpisodeSerializer,
        "update": CreateEpisodeSerializer,
        "retrieve": EpisodeSerializer,
        "partial_update": CreateEpisodeSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(EpisodeViewSet, self).get_serializer_class()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = EpisodeSerializer(Episode.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)


class SeasonViewSet(viewsets.ModelViewSet):
    serializer_class = SeasonSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Season.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    filter_class = SeasonFilter
    search_fields = ("title",)

    action_serializer_classes = {
        "create": CreateSeasonSerializer,
        "update": CreateSeasonSerializer,
        "retrieve": SeasonSerializer,
        "partial_update": CreateSeasonSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(SeasonViewSet, self).get_serializer_class()

    @list_route(methods=['get'])
    def check_season(self, request):
        title = request.query_params.get("title", None)
        series = request.query_params.get("series", None)
        qs = Season.objects.filter(title=title, series=series)

        season_serialiser = SeasonSerializer(
            qs, context={"request": request}, many=True)
        return Response(season_serialiser.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = SeasonSerializer(Season.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)


class SeriesViewSet(viewsets.ModelViewSet):
    serializer_class = DetailedSeriesSerializer
    permission_classes = (CustomDjangoContentPermission,)
    queryset = Series.objects.all().order_by('created_on')
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = SeriesFilter
    search_fields = ("title", "seasons__title", "seasons__episodes__title",
                     "seasons__episodes__asset_version__title", "seasons__episodes__asset_version__video__title")
    action_serializer_classes = {
        "create": CreateSeriesSerializer,
        "update": CreateSeriesSerializer,
        "retrieve": DetailedSeriesSerializer,
        "partial_update": CreateSeriesSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):

        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(SeriesViewSet, self).get_serializer_class()

    # @list_route(methods=['get'])
    # def check_series(self, request):
    # 	title = request.query_params.get("title", None)
    # 	if title:
    # 		qs = Series.objects.filter(title=title)
    # 		series_serialiser = SeriesSerializer(qs, context={"request":request}, many=True)
    # 		return Response(series_serialiser.data, status=status.HTTP_200_OK)
    # 	else:
    # return Response(data={"message": "Error in
    # data"},status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'])
    def add_episode(self, request):
        tmp = urllib.parse.parse_qs(request.body.decode('utf-8'))
        logging.info(tmp)
        title = tmp['title'][0].replace("+", " ")
        vid = tmp['vid'][0]
        m, c = Series.objects.get_or_create(series_title=title)
        if vid:
            try:
                v = Video.objects.get(id=vid)
                title = v.title
                episode_title = title.replace(".mp4", "")
                try:
                    episode_number = re.search(
                        "([0-9])+", episode_title).group(0)
                except AttributeError:
                    episode_number = 0
                eps, c = Episode.objects.get_or_create(episode_title=episode_title, channel=m.channel,
                                                       episode_number=episode_number, series=m)
                eps_seg = EpisodeSegment.objects.create(episode=eps, video=v)
                return Response(data={"message": "successful creation"}, status=status.HTTP_201_CREATED)
            except ObjectDoesNotExist:
                pass
        return Response(data={"message": "Error in data"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = DetailedSeriesSerializer(Series.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)

    # To accomodate Channel based permissions
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_content_by_channel(queryset, request)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ChannelViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelSerializer
    permission_classes = (CustomDjangoContentPermission, IsAuthenticated,)
    queryset = Channel.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = ChannelFilter

    search_fields = ("channel_name",)

    # To accomodate Channel based permissions
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        user_all_memberships = WorkGroupMembership.objects.filter(
            user=request.user)
        user_all_roles = Role.objects.filter(
            workgroupmembership__in=user_all_memberships)
        user_all_perms = list(Permission.objects.filter(
            role__in=user_all_roles).values_list("codename", flat=True))
        channels = Channel.objects.all()
        channel_perms = ["can_access_{}".format(
            channel.channel_name.lower().replace(" ", "_")) for channel in channels]
        allowed_channel_perms = list(
            filter(lambda x: x in user_all_perms, channel_perms))
        allowed_channels = [x.replace("can_access_", "").replace(
            "_", " ") for x in allowed_channel_perms]
        if allowed_channels and not request.user.is_superuser:
            query = reduce(operator.or_, (Q(channel_name__iexact=x)
                                          for x in allowed_channels))
            queryset = queryset.filter(query)
        elif not request.user.is_superuser:
            queryset = queryset.filter(pk__isnull=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ContextTypeViewSet(viewsets.ModelViewSet):
    serializer_class = ContextTypeSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ContextType.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    filter_class = ContextTypeFilter
    search_fields = ("type_name",)


class TVAnchorViewSet(viewsets.ModelViewSet):
    serializer_class = TVAnchorSerializer
    permission_classes = (IsAuthenticated,)
    queryset = TVAnchor.objects.all().order_by('-created_on')
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = TVAnchorFilter
    search_fields = ('person__name', 'organizations',
                     "notable_credits", "awards", "books")
    action_serializer_classes = {
        "create": CreateTVAnchorSerializer,
        "update": CreateTVAnchorSerializer
    }

    def get_serializer_class(self):

        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(TVAnchorViewSet, self).get_serializer_class()


class MovieViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSerializer
    permission_classes = (CustomDjangoModelPermission,)
    queryset = Movie.objects.all().prefetch_related(
        'moviesegment_set').prefetch_related('movietranslationjob_set')
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    # filter_class = MovieFilter
    search_fields = ("title", "channel__channel_name")
    filter_fields = ("channel",)
    action_serializer_classes = {
        "create": CreateMovieSerializer,
        "update": CreateMovieSerializer,
        "retrieve": MovieSerializer,
        "list": MovieSerializer,
        "partial_update": CreateMovieSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(MovieViewSet, self).get_serializer_class()

    # def list(self, request):
    # 	"""To accomodate created_on on date"""
    # 	page_size = int(request.query_params.get("page_size", 10))
    # 	search = request.query_params.get("search", None)
    # 	created_on = request.query_params.get("created_on", None)
    # 	page = int(request.query_params.get("page", 1))
    # 	qs = self.get_queryset()
    # 	if created_on:
    # 		qs = qs.filter(created_on__date=created_on)
    # 	if search:
    # 		qs = qs.filter(movie_title__icontains=search)
    # 	qs = qs.order_by('-created_on')
    # 	ser = MovieSerializer(qs[(page-1)*page_size:page*page_size], many=True, context={'request':request})

    # 	count = qs.count()
    # 	total_pages = math.ceil(count/page_size)

    # 	return Response(data={"count":count, "page":page, "total_pages": total_pages,
    # 								   "page_size":page_size, "results":ser.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = MovieSerializer(Movie.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)

    @list_route(methods=['get'])
    def library(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_content_by_channel(queryset, request)

        """
		Filter Logic begins
		"""
        genres = request.query_params.get('genre', None)
        if genres:
            genres = genres.split(",")

        dates = request.query_params.get('created_on', None)
        start_date = None
        end_date = None
        if dates:
            start_date = dates.split(",")[0] if dates else None
            end_date = dates.split(",")[1] if dates else None

        ingest_date = request.query_params.get('ingested_on', None)
        ingest_start_date = None
        ingest_end_date = None
        if ingest_date:
            ingest_start_date = ingest_date.split(
                ",")[0] if ingest_date else None
            ingest_end_date = ingest_date.split(
                ",")[1] if ingest_date else None

        channel = request.query_params.get('channel', None)

        is_active = request.query_params.get('is_active', None)
        is_active = None if not is_active else (
            True if is_active and is_active == "true" else False)

        is_tagged = request.query_params.get('is_tagged', None)
        is_tagged = None if not is_tagged else (
            True if is_tagged and is_tagged == "true" else False)

        search = request.query_params.get('search', None)

        kwargs = {
            '{0}__{1}'.format('genre', 'in'): genres,
            '{0}'.format('channel'): channel,
            '{0}__{1}__{2}'.format('created_on', 'date', 'gte'): start_date,
            '{0}__{1}__{2}'.format('created_on', 'date', 'lte'): end_date,
            '{0}__{1}'.format('ingested_on', 'gte'): ingest_start_date,
            '{0}__{1}'.format('ingested_on', 'lte'): ingest_end_date,
        }

        # remove all values having None values
        kwargs_dict = {k: v for k, v in kwargs.items() if v is not None}
        queryset = queryset.filter(**kwargs_dict)

        query = None
        if is_active is not None:
            query = Q(asset_version__proxy_type="SRC") & Q(
                asset_version__is_active=is_active)

        if is_tagged is not None:
            query = Q(asset_version__proxy_type="SRC") & Q(
                asset_version__is_tagged=is_tagged)

        if query != None:
            queryset = queryset.filter(query)

        if search:
            query = (Q(title__iexact=search) | Q(asset_version__title__iexact=search) | Q(
                asset_version__video__title__iexact=search))
            qs = queryset.filter(query)
            if qs.count() == 0:
                query = (Q(title__icontains=search) | Q(asset_version__title__icontains=search) | Q(
                    asset_version__video__title__icontains=search))
                qs = queryset.filter(query)
            queryset = qs

        """
		Filter Logic ends
		"""

        page = self.paginate_queryset(queryset)
        if page is not None:
            asset_list = []
            for asset in page:
                asset_res = CognitiveSearchMovieSerializer(
                    asset, context={'request': request}).data
                query = Q(object_id=asset.id) & Q(proxy_type="SRC")

                if is_active is not None:
                    query &= Q(is_active=is_active)

                if is_tagged is not None:
                    query &= Q(is_tagged=is_tagged)

                asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.all().filter(
                    query).distinct().order_by('-created_on'), many=True, context={'request': request}).data
                asset_res["asset_version"] = asset_version
                asset_list.append(asset_res)
            return self.get_paginated_response(asset_list)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # To accomodate Channel based permissions
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_content_by_channel(queryset, request)

        """
		Filter Logic begins
		"""
        genres = request.query_params.get('genre', None)
        if genres:
            genres = genres.split(",")

        dates = request.query_params.get('created_on', None)
        start_date = None
        end_date = None
        if dates:
            start_date = dates.split(",")[0] if dates else None
            end_date = dates.split(",")[1] if dates else None

        assigned_to = request.query_params.get('assigned_to', None)

        is_assigned = request.query_params.get('is_assigned', None)
        is_assigned = None if not is_assigned else (
            True if is_assigned and is_assigned == "true" else False)

        ingest_date = request.query_params.get('ingested_on', None)
        ingest_start_date = None
        ingest_end_date = None
        if ingest_date:
            ingest_start_date = ingest_date.split(
                ",")[0] if ingest_date else None
            ingest_end_date = ingest_date.split(
                ",")[1] if ingest_date else None

        channel = request.query_params.get('channel', None)

        is_active = request.query_params.get('is_active', None)
        is_active = None if not is_active else (
            True if is_active and is_active == "true" else False)

        is_tagged = request.query_params.get('is_tagged', None)
        is_tagged = None if not is_tagged else (
            True if is_tagged and is_tagged == "true" else False)

        workflow = request.query_params.get('workflow', None)

        search = request.query_params.get('search', None)

        kwargs = {
            '{0}__{1}'.format('genre', 'in'): genres,
            '{0}'.format('channel'): channel,
            '{0}__{1}'.format('asset_version', 'is_tagged'): is_tagged,
            '{0}__{1}'.format('asset_version', 'is_active'): is_active,
            '{0}__{1}__{2}'.format('created_on', 'date', 'gte'): start_date,
            '{0}__{1}__{2}'.format('created_on', 'date', 'lte'): end_date,
            '{0}__{1}'.format('ingested_on', 'gte'): ingest_start_date,
            '{0}__{1}'.format('ingested_on', 'lte'): ingest_end_date,
        }

        # remove all values having None values
        kwargs_dict = {k: v for k, v in kwargs.items() if v is not None}
        queryset = queryset.filter(**kwargs_dict)

        # For Manual Tagging platform which doesnt require workflow integration
        if is_tagged is not None:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        # keep workflow=None condition
        user_all_memberships = WorkGroupMembership.objects.filter(
            user=request.user)
        user_all_workgroups = WorkGroup.objects.filter(
            members__in=user_all_memberships)

        # Show only those assets whose workflow contains my workgroup
        query = None
        if not request.user.is_superuser:
            query = Q(asset_version__work_flow_instances__work_flow=workflow) & Q(
                asset_version__work_flow_instances__work_flow_instance_steps__work_flow_step__workgroup__in=user_all_workgroups)
        else:
            query = Q(asset_version__work_flow_instances__work_flow=workflow)

        if workflow is not None and is_assigned is not None:
            if is_assigned == True:
                query &= Q(
                    asset_version__work_flow_instances__work_flow_instance_steps__assigned__isnull=False)
            else:
                query &= Q(
                    asset_version__work_flow_instances__work_flow_instance_steps__assigned__isnull=True)

        if workflow is not None and assigned_to is not None:
            query &= Q(
                asset_version__work_flow_instances__work_flow_instance_steps__assigned__assigned_to=assigned_to)

        queryset = queryset.filter(query).distinct()

        if search:
            query = (Q(title__iexact=search) | Q(asset_version__title__iexact=search) | Q(
                asset_version__video__title__iexact=search))
            qs = queryset.filter(query)
            if qs.count() == 0:
                query = (Q(title__icontains=search) | Q(asset_version__title__icontains=search) | Q(
                    asset_version__video__title__icontains=search))
                qs = queryset.filter(query)
            queryset = qs

        """
		Filter Logic ends
		"""

        page = self.paginate_queryset(queryset)
        if page is not None:
            asset_list = []
            for asset in page:
                asset_res = CognitiveSearchMovieSerializer(
                    asset, context={'request': request}).data
                query = Q(object_id=asset.id) & Q(
                    work_flow_instances__work_flow=workflow)

                if not request.user.is_superuser:
                    query &= Q(
                        work_flow_instances__work_flow_instance_steps__work_flow_step__workgroup__in=user_all_workgroups)

                if is_active is not None:
                    query &= Q(is_active=is_active)

                if workflow is not None and is_assigned is not None:
                    if is_assigned == True:
                        query &= Q(
                            work_flow_instances__work_flow_instance_steps__assigned__isnull=False)
                    else:
                        query &= Q(
                            work_flow_instances__work_flow_instance_steps__assigned__isnull=True)

                if workflow is not None and assigned_to is not None:
                    query &= Q(
                        work_flow_instances__work_flow_instance_steps__assigned__assigned_to=assigned_to)

                asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.all().filter(
                    query).distinct().order_by('-created_on'), many=True, context={'request': request}).data
                asset_res["asset_version"] = asset_version
                asset_list.append(asset_res)
            return self.get_paginated_response(asset_list)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['post'])
    def add_movie_segment(self, request):

        tmp = urllib.parse.parse_qs(request.body.decode('utf-8'))
        logging.info(tmp)
        title = tmp['title'][0].replace("+", " ")
        vid = tmp['vid'][0]
        m, c = Movie.objects.get_or_create(movie_title=title)
        if vid:
            try:
                v = Video.objects.get(id=vid)
                m_seg = MovieSegment.objects.create(movie=m, video=v)
                return Response(data={"message": "successful creation"}, status=status.HTTP_201_CREATED)
            except ObjectDoesNotExist:
                pass
        return Response(data={"message": "Error in data"}, status=status.HTTP_400_BAD_REQUEST)


class PromoViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset for Promos
    """
    serializer_class = DetailedPromoSerializer
    queryset = Promo.objects.all().order_by('-ingested_on')
    permission_classes = (CustomDjangoContentPermission,)
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = PromoFilter
    search_fields = ('title', 'asset_version__title',
                     'asset_version__video__title')
    pagination_class = ShortResultsSetPagination

    action_serializer_classes = {
        "create": PromoSerializer,
        "update": PromoSerializer,
        "retrieve": DetailedPromoSerializer,
        "list": DetailedPromoSerializer,
        "partial_update": PromoSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(PromoViewSet, self).get_serializer_class()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = DetailedPromoSerializer(Promo.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)

    @list_route(methods=['get'])
    def library(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_content_by_channel(queryset, request)

        """
		Filter Logic begins
		"""
        genres = request.query_params.get('genre', None)
        if genres:
            genres = genres.split(",")

        dates = request.query_params.get('created_on', None)
        start_date = None
        end_date = None
        if dates:
            start_date = dates.split(",")[0] if dates else None
            end_date = dates.split(",")[1] if dates else None

        ingest_date = request.query_params.get('ingested_on', None)
        ingest_start_date = None
        ingest_end_date = None
        if ingest_date:
            ingest_start_date = ingest_date.split(
                ",")[0] if ingest_date else None
            ingest_end_date = ingest_date.split(
                ",")[1] if ingest_date else None

        channel = request.query_params.get('channel', None)

        is_active = request.query_params.get('is_active', None)
        is_active = None if not is_active else (
            True if is_active and is_active == "true" else False)

        is_tagged = request.query_params.get('is_tagged', None)
        is_tagged = None if not is_tagged else (
            True if is_tagged and is_tagged == "true" else False)

        search = request.query_params.get('search', None)

        kwargs = {
            '{0}__{1}'.format('genre', 'in'): genres,
            '{0}'.format('channel'): channel,
            '{0}__{1}__{2}'.format('created_on', 'date', 'gte'): start_date,
            '{0}__{1}__{2}'.format('created_on', 'date', 'lte'): end_date,
            '{0}__{1}'.format('ingested_on', 'gte'): ingest_start_date,
            '{0}__{1}'.format('ingested_on', 'lte'): ingest_end_date,
        }

        # remove all values having None values
        kwargs_dict = {k: v for k, v in kwargs.items() if v is not None}
        queryset = queryset.filter(**kwargs_dict)

        query = None
        if is_active is not None:
            query = Q(asset_version__proxy_type="SRC") & Q(
                asset_version__is_active=is_active)

        if is_tagged is not None:
            query = Q(asset_version__proxy_type="SRC") & Q(
                asset_version__is_tagged=is_tagged)

        if query != None:
            queryset = queryset.filter(query)

        if search:
            query = (Q(title__iexact=search) | Q(asset_version__title__iexact=search) | Q(
                asset_version__video__title__iexact=search))
            qs = queryset.filter(query)
            if qs.count() == 0:
                query = (Q(title__icontains=search) | Q(asset_version__title__icontains=search) | Q(
                    asset_version__video__title__icontains=search))
                qs = queryset.filter(query)
            queryset = qs

        """
		Filter Logic ends
		"""

        page = self.paginate_queryset(queryset)
        if page is not None:
            asset_list = []
            for asset in page:
                asset_res = CognitiveSearchPromoSerializer(
                    asset, context={'request': request}).data
                query = Q(object_id=asset.id) & Q(proxy_type="SRC")

                if is_active is not None:
                    query &= Q(is_active=is_active)

                if is_tagged is not None:
                    query &= Q(is_tagged=is_tagged)

                asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.all().filter(
                    query).distinct().order_by('-created_on'), many=True, context={'request': request}).data
                asset_res["asset_version"] = asset_version
                asset_list.append(asset_res)
            return self.get_paginated_response(asset_list)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # To accomodate Channel based permissions
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_content_by_channel(queryset, request)

        """
		Filter Logic begins
		"""
        genres = request.query_params.get('genre', None)
        if genres:
            genres = genres.split(",")

        dates = request.query_params.get('created_on', None)
        start_date = None
        end_date = None
        if dates:
            start_date = dates.split(",")[0] if dates else None
            end_date = dates.split(",")[1] if dates else None

        assigned_to = request.query_params.get('assigned_to', None)

        is_assigned = request.query_params.get('is_assigned', None)
        is_assigned = None if not is_assigned else (
            True if is_assigned and is_assigned == "true" else False)

        ingest_date = request.query_params.get('ingested_on', None)
        ingest_start_date = None
        ingest_end_date = None
        if ingest_date:
            ingest_start_date = ingest_date.split(
                ",")[0] if ingest_date else None
            ingest_end_date = ingest_date.split(
                ",")[1] if ingest_date else None

        channel = request.query_params.get('channel', None)

        is_active = request.query_params.get('is_active', None)
        is_active = None if not is_active else (
            True if is_active and is_active == "true" else False)

        is_tagged = request.query_params.get('is_tagged', None)
        is_tagged = None if not is_tagged else (
            True if is_tagged and is_tagged == "true" else False)

        workflow = request.query_params.get('workflow', None)

        search = request.query_params.get('search', None)

        kwargs = {
            '{0}__{1}'.format('genre', 'in'): genres,
            '{0}'.format('channel'): channel,
            '{0}__{1}'.format('asset_version', 'is_tagged'): is_tagged,
            '{0}__{1}'.format('asset_version', 'is_active'): is_active,
            '{0}__{1}__{2}'.format('created_on', 'date', 'gte'): start_date,
            '{0}__{1}__{2}'.format('created_on', 'date', 'lte'): end_date,
            '{0}__{1}'.format('ingested_on', 'gte'): ingest_start_date,
            '{0}__{1}'.format('ingested_on', 'lte'): ingest_end_date,
        }

        # remove all values having None values
        kwargs_dict = {k: v for k, v in kwargs.items() if v is not None}
        queryset = queryset.filter(**kwargs_dict)

        # For Manual Tagging platform which doesnt require workflow integration
        if is_tagged is not None:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        # keep workflow=None condition
        user_all_memberships = WorkGroupMembership.objects.filter(
            user=request.user)
        user_all_workgroups = WorkGroup.objects.filter(
            members__in=user_all_memberships)

        # Show only those assets whose workflow contains my workgroup
        query = None
        if not request.user.is_superuser:
            query = Q(asset_version__work_flow_instances__work_flow=workflow) & Q(
                asset_version__work_flow_instances__work_flow_instance_steps__work_flow_step__workgroup__in=user_all_workgroups)
        else:
            query = Q(asset_version__work_flow_instances__work_flow=workflow)

        if workflow is not None and is_assigned is not None:
            if is_assigned == True:
                query &= Q(
                    asset_version__work_flow_instances__work_flow_instance_steps__assigned__isnull=False)
            else:
                query &= Q(
                    asset_version__work_flow_instances__work_flow_instance_steps__assigned__isnull=True)

        if workflow is not None and assigned_to is not None:
            query &= Q(
                asset_version__work_flow_instances__work_flow_instance_steps__assigned__assigned_to=assigned_to)

        queryset = queryset.filter(query).distinct()

        if search:
            query = (Q(title__iexact=search) | Q(asset_version__title__iexact=search) | Q(
                asset_version__video__title__iexact=search))
            qs = queryset.filter(query)
            if qs.count() == 0:
                query = (Q(title__icontains=search) | Q(asset_version__title__icontains=search) | Q(
                    asset_version__video__title__icontains=search))
                qs = queryset.filter(query)
            queryset = qs

        """
		Filter Logic ends
		"""

        page = self.paginate_queryset(queryset)
        if page is not None:
            asset_list = []
            for asset in page:
                asset_res = CognitiveSearchPromoSerializer(
                    asset, context={'request': request}).data
                query = Q(object_id=asset.id) & Q(
                    work_flow_instances__work_flow=workflow)

                if not request.user.is_superuser:
                    query &= Q(
                        work_flow_instances__work_flow_instance_steps__work_flow_step__workgroup__in=user_all_workgroups)

                if is_active is not None:
                    query &= Q(is_active=is_active)

                if workflow is not None and is_assigned is not None:
                    if is_assigned == True:
                        query &= Q(
                            work_flow_instances__work_flow_instance_steps__assigned__isnull=False)
                    else:
                        query &= Q(
                            work_flow_instances__work_flow_instance_steps__assigned__isnull=True)

                if workflow is not None and assigned_to is not None:
                    query &= Q(
                        work_flow_instances__work_flow_instance_steps__assigned__assigned_to=assigned_to)

                asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.all().filter(
                    query).distinct().order_by('-created_on'), many=True, context={'request': request}).data
                asset_res["asset_version"] = asset_version
                asset_list.append(asset_res)
            return self.get_paginated_response(asset_list)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class NxMovieViewSet(viewsets.ModelViewSet):
    serializer_class = NxMovieSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Movie.objects.all().filter(trivia__isnull=False).distinct().\
        annotate(pending_trivia=models.Sum(models.Case(models.When(trivia__edit_status='CLN', then=1), default=0,
                                                       output_field=models.IntegerField()))).order_by('-pending_trivia')
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    filter_class = MovieFilter
    search_fields = ("movie_title", 'channel__channel_name')
    action_serializer_classes = {
        "create": CreateMovieSerializer,
        "update": CreateMovieSerializer,
        "retrieve": MovieSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(NxMovieViewSet, self).get_serializer_class()


class MovieSegmentViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSegmentSerializer
    permission_classes = (IsAuthenticated,)
    queryset = MovieSegment.objects.all()
    filter_backends = (filters.SearchFilter, )
    search_fields = ('video__title', "movie__movie_title")
    action_serializer_classes = {
        "create": CreateMovieSegmentSerializer,
        "update": CreateMovieSegmentSerializer,
        "retrieve": MovieSegmentSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(MovieSegmentViewSet, self).get_serializer_class()


class EpisodeSegmentViewSet(viewsets.ModelViewSet):
    serializer_class = EpisodeSegmentSerializer
    permission_classes = (IsAuthenticated,)
    queryset = EpisodeSegment.objects.all()
    filter_backends = (filters.SearchFilter, )
    search_fields = ("episode__series__series_title", 'video__title',
                     'episode__episode_title', "episode__channel__channel_name")
    action_serializer_classes = {
        "create": CreateEpisodeSegmentSerializer,
        "update": CreateEpisodeSegmentSerializer,
        "retrieve": EpisodeSegmentSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(EpisodeSegmentViewSet, self).get_serializer_class()


class TriviaViewSet(LoggingMixin, viewsets.ModelViewSet):
    logging_methods = ['POST', 'PUT']
    serializer_class = DetailTriviaSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Trivia.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    filter_class = TriviaFilter
    search_fields = ("trivia", 'movie__movie_title', "persons__name")
    action_serializer_classes = {
        "create": CreateTriviaSerializer,
        "update": CreateTriviaSerializer,
        "retrieve": DetailTriviaSerializer,
    }
    pagination_class = CustomPagination

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(TriviaViewSet, self).get_serializer_class()

    @list_route(methods=['get'])
    def me(self, request):
        qs = self.queryset.filter(created_by=request.user)
        ser = TriviaSerializer(qs, many=True, context={'request': request})
        return Response(data=ser.data, status=status.HTTP_200_OK)

    @list_route(methods=['get'], permission_classes=[IsAdminUser, ])
    def stat_all(self, request):
        users = Trivia.objects.all().values("created_by").distinct()
        data = []
        for user in users:
            if user['created_by']:
                dp = {
                    'user': user['created_by']
                }
                dp_user = User.objects.get(id=user['created_by'])
                dp['user_name'] = dp_user.first_name + " " + dp_user.last_name
                total = Trivia.objects.filter(created_by=dp_user).count()
                time_before_24hrs = datetime.now() - timedelta(hours=24)
                time_before_week = datetime.now() - timedelta(hours=168)
                today = Trivia.objects.filter(Q(created_by=dp_user) & Q(
                    modified_on__gte=time_before_24hrs)).count()
                weekly = Trivia.objects.filter(Q(created_by=dp_user) & Q(
                    modified_on__gte=time_before_week)).count()
                dp['today'] = today
                dp['total'] = total
                dp['weekly'] = weekly
                data.append(dp)
        return Response(data=data, status=status.HTTP_200_OK)

    @list_route(methods=['post'])
    def load(self, request):
        data = request.data
        ser = LoadTriviaSerializer(data=data)
        if ser.is_valid():
            ser_data = ser.data
            # find person with same name
            try:
                person, c = Person.objects.get_or_create(
                    name=ser_data['actor_name'])
                if c:
                    person.occupation = ser_data['occupation']
                    person.save()
            except MultipleObjectsReturned:
                person = Person.objects.filter(
                    name=ser_data['actor_name']).first()
            # create trivia object
            ind = 0
            for trivia in ser_data['trivia']:
                t_obj = Trivia.objects.create(trivia=trivia)
                t_obj.original_description = ser_data[
                    'original_description'][ind]
                t_obj.persons.add(person)
                t_obj.save()
            return Response(data=ser.data, status=status.HTTP_201_CREATED)
        return Response(data={"response": "failed"}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'])
    def load_for_movie(self, request):
        data = request.data
        ser = LoadMovieTriviaSerializer(data=data)
        if ser.is_valid():
            ser_data = ser.data
            # find person with same name
            if ser_data['year']:
                movie, c = Movie.objects.get_or_create(
                    movie_title=ser_data['name'], year_of_release="{}-01-01".format(ser_data['year']))
            else:
                movie, c = Movie.objects.get_or_create(
                    movie_title=ser_data['name'])
            # create trivia object
            ind = 0
            for trivia in ser_data['trivia']:
                t_obj, c = Trivia.objects.get_or_create(trivia=trivia)
                if c:
                    t_obj.movie.add(movie)
                    t_obj.original_description = ser_data[
                        'original_description'][ind]
                    t_obj.is_approved = "false"
                    t_obj.save()
                ind += 1

            return Response(data=ser.data, status=status.HTTP_201_CREATED)
        return Response(data={"response": "failed"}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'])
    def update_for_movie(self, request):
        data = request.data
        ser = LoadMovieTriviaSerializer(data=data)
        if ser.is_valid():
            ser_data = ser.data
            # find person with same name
            if ser_data['year']:
                movie, c = Movie.objects.get_or_create(movie_title=ser_data['name'],
                                                       year_of_release="{}-01-01".format(ser_data['year']))
            else:
                movie, c = Movie.objects.get_or_create(
                    movie_title=ser_data['name'])
            # create trivia object
            ind = 0
            for trivia in ser_data['original_description']:
                try:
                    if trivia != 'Old Trivia':
                        t_obj = Trivia.objects.get(original_description=trivia)
                        if not t_obj.movie.count():
                            t_obj.movie.add(movie)
                            t_obj.is_approved = "false"
                            t_obj.save()
                except ObjectDoesNotExist:
                    pass
                except MultipleObjectsReturned:
                    pass
                ind += 1

            return Response(data=ser.data, status=status.HTTP_201_CREATED)
        return Response(data={"response": "failed"}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'])
    def update_trivia(self, request):
        data = request.data
        ser = UpdateTriviaSerializer(data=data)
        if ser.is_valid():
            ser_data = ser.data
            # find person with same name
            person, c = Person.objects.get_or_create(
                name=ser_data['actor_name'])
            if c:
                person.occupation = "Actor"
                person.save()
            # create trivia object
            count = 0
            for trivia in ser_data['original']:
                count += 1
                try:
                    t_obj = Trivia.objects.get(original_description=trivia)
                    t_obj.trivia = ser_data['trivia'][count - 1]
                    t_obj.save()
                except MultipleObjectsReturned:
                    t_obj = Trivia.objects.filter(original_description=trivia)
                    for t_o in t_obj:
                        t_o.trivia = ser_data['trivia'][count - 1]
                        t_o.save()
                except ObjectDoesNotExist:
                    pass

            return Response(data=ser.data, status=status.HTTP_201_CREATED)

    @list_route(methods=['get'])
    def next(self, request):
        trivia_list = Trivia.objects.filter(trivia=F('original_description'))
        count = trivia_list.count()
        if count:
            index = math.floor(count * random.random())
            trivia_obj = trivia_list[index]
            ser = TriviaSerializer(trivia_obj, context={
                                   'request': self.request})
            return Response(data=ser.data, status=status.HTTP_200_OK)
        else:
            return Response(data=[], status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def stat(self, request):
        total = Trivia.objects.filter(created_by=request.user).count()
        time_before_24hrs = datetime.now() - timedelta(hours=24)
        today = Trivia.objects.filter(Q(created_by=request.user) & Q(
            modified_on__gte=time_before_24hrs)).count()
        return Response(data={"total": total, "today": today}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def approval_stat(self, request):
        total = Trivia.objects.filter(approved_by=request.user).count()
        time_before_24hrs = datetime.now() - timedelta(hours=24)
        today = Trivia.objects.filter(Q(approved_by=request.user) & Q(
            modified_on__gte=time_before_24hrs)).count()
        return Response(data={"total": total, "today": today}, status=status.HTTP_200_OK)

    @list_route(methods=['get'], permission_classes=[IsAdminUser, ])
    def approval_stat_all(self, request):
        users = Trivia.objects.all().values("approved_by").distinct()
        data = []
        for user in users:
            if user['approved_by']:
                dp = {
                    'user': user['approved_by']
                }
                dp_user = User.objects.get(id=user['approved_by'])
                dp['user_name'] = dp_user.first_name + " " + dp_user.last_name
                total = Trivia.objects.filter(approved_by=dp_user).count()
                time_before_24hrs = datetime.now() - timedelta(hours=24)
                today = Trivia.objects.filter(Q(approved_by=dp_user) & Q(
                    modified_on__gte=time_before_24hrs)).count()
                dp['today'] = today
                dp['total'] = total
                data.append(dp)
        return Response(data=data, status=status.HTTP_200_OK)

    @list_route(methods=['post'], permission_classes=[IsAdminUser, ])
    def load_trivia_generic(self, request):
        data = request.data
        ser = LoadGenericTriviaSerializer(data=data)
        if ser.is_valid():
            ser_data = ser.data
            # logging.error(ser_data)
            # find actors
            persons = []
            for actor in ser_data['actors']:
                person = None
                try:
                    person, c = Person.objects.get_or_create(name=actor)
                    if c:
                        person.occupation = 'Actor'
                        person.save()
                except MultipleObjectsReturned:
                    person = Person.objects.filter(name=actor).first()
                if person:
                    persons.append(person)
            for singer in ser_data['singers']:
                person = None
                try:
                    person, c = Person.objects.get_or_create(name=singer)
                    if c:
                        person.occupation = 'Singer'
                        person.save()
                except MultipleObjectsReturned:
                    person = Person.objects.filter(name=singer).first()
                if person:
                    persons.append(person)
            if ser_data['director']:
                person = None
                try:
                    person, c = Person.objects.get_or_create(
                        name=ser_data['director'])
                    if c:
                        person.occupation = 'Director'
                        person.save()
                except MultipleObjectsReturned:
                    person = Person.objects.filter(
                        name=ser_data['director']).first()
                if person:
                    persons.append(person)
            movie = None
            if ser_data['movie']:
                movie, m_c = Movie.objects.get_or_create(
                    movie_title=ser_data['movie'])
            # create trivia object
            ind = 0
            # logging.error(ser_data['trivia'])
            for trivia in ser_data['trivia']:
                t_obj, c = Trivia.objects.get_or_create(trivia=trivia)
                # logging.error(t_obj, c)
                if c:
                    t_obj.original_description = ser_data[
                        'original_description'][ind]
                    t_obj.is_approved = ser_data['is_approved']
                    t_obj.edit_status = ser_data['is_approved']
                    t_obj.approved_by = request.user
                    if movie:
                        t_obj.movie.add(movie)

                    for person in persons:
                        t_obj.persons.add(person)
                    t_obj.save()
                else:
                    t_obj.original_description = ser_data[
                        'original_description'][ind]
                    t_obj.is_approved = ser_data['is_approved']
                    t_obj.edit_status = ser_data['is_approved']
                    if movie:
                        t_obj.movie.add(movie)
                    for person in persons:
                        t_obj.persons.add(person)
                    t_obj.save()
                ind += 1
            return Response(data={"count": str(ind)}, status=status.HTTP_200_OK)
        return Response(data={"response": "failed"}, status=status.HTTP_400_BAD_REQUEST)


class ActorViewSet(viewsets.ModelViewSet):
    serializer_class = DetailActorSerializer
    queryset = Actor.objects.all()
    permission_classes = (IsAuthenticated,)


class PersonGroupViewSet(viewsets.ModelViewSet):
    serializer_class = PersonGroupSerializer
    queryset = PersonGroup.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("title",)
    action_serializer_classes = {
        "create": CreatePersonGroupSerializer,
        "update": CreatePersonGroupSerializer,
        "retrieve": PersonGroupSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(PersonGroupViewSet, self).get_serializer_class()


class PlaylistViewSet(viewsets.ModelViewSet):
    serializer_class = PlaylistSerializer
    queryset = Playlist.objects.all().order_by("-date")
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    search_fields = ('channel__channel_name',)
    filter_fields = ("channel", "date")

    action_serializer_classes = {
        "list": DetailPlaylistSerializer,
        "create": PlaylistSerializer,
        "update": PlaylistSerializer,
        "retrieve": DetailPlaylistSerializer,
    }

    def get_serializer_context(self):

        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(PlaylistViewSet, self).get_serializer_class()

    @list_route(methods=['get'])
    def channels(self, request, **kwargs):
        qs = self.get_queryset()
        latest_channel = qs.order_by(
            "channel__id", "-date").distinct("channel__id")
        data = DetailPlaylistSerializer(latest_channel, many=True)
        return Response(data=data.data, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def solo(self, request, **kwargs):
        qs = self.get_queryset()
        channel = request.query_params.get("channel", None)
        date = request.query_params.get("date", None)
        if channel:
            qs = qs.filter(channel__id=channel)
        if date:
            qs = qs.filter(date=date)
        ser = DetailPlaylistSerializer(qs, many=True)
        return Response(data=ser.data, status=status.HTTP_200_OK)

    # stats for each playlist


class PlaylistDate(viewsets.ViewSet):
    queryset = Playlist.objects.all()

    def list(self, request, *args, **kwargs):
        unique_dates = self.queryset.values('date').distinct()
        data = []
        for dat in unique_dates:
            data.append(dat['date'])
        return Response(data=data, status=status.HTTP_200_OK)


class PlaylistEntryViewSet(viewsets.ModelViewSet):
    serializer_class = PlaylistEntrySerializer
    queryset = PlaylistEntry.objects.all()
    filter_backends = (filters.DjangoObjectPermissionsFilter,
                       filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    search_fields = ('playlist__channel__channel_name',
                     'content_object__title')


class SongViewSet(viewsets.ModelViewSet):
    serializer_class = DetailSongSerializer
    queryset = Song.objects.all()
    permission_classes = (CustomDjangoModelPermission,)
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    search_fields = ('title',)

    action_serializer_classes = {
        "create": SongSerializer,
        "update": SongSerializer,
        "retrieve": DetailSongSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(SongViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        complete_ser = DetailSongSerializer(
            Song.objects.get(id=serializer.data['id']))
        return Response(complete_ser.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request):
        """To accomodate created_on on date"""
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", None)
        created_on = request.query_params.get("created_on", None)
        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        if search:
            qs = qs.filter(title__icontains=search)
        qs = qs.order_by('-created_on')
        ser = DetailSongSerializer(
            qs[(page - 1) * page_size:page * page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count / page_size)

        return Response(data={"count": count, "page": page, "total_pages": total_pages,
                              "page_size": page_size, "results": ser.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = DetailSongSerializer(
            Song.objects.get(id=serializer.data['id']))
        return Response(complete_ser.data)


class TriviaLogViewSet(viewsets.ModelViewSet):
    serializer_class = TriviaLogSerializer
    queryset = TriviaLog.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter)
    search_fields = ('trivia', 'playlist_entry__content_object__title')
    ordering_fields = ('trivia__trivia', 'timestamp',
                       'playlist_entry__start_time')
    action_serializer_classes = {
        "create": CreateTriviaLogSerializer,
        "update": CreateTriviaLogSerializer,
        "retrieve": TriviaLogSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(TriviaLogViewSet, self).get_serializer_class()


class LabelViewSet(viewsets.ModelViewSet):
    serializer_class = LabelSerializer
    queryset = Label.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    search_fields = ('name',)


class TriviaEditLogViewSet(viewsets.ModelViewSet):
    serializer_class = TriviaEditLogSerializer
    queryset = TriviaEditLog.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    filter_class = TriviaEditLogFilter
    search_fields = ("trivia__trivia", 'user__username',
                     "trivia_before", "trivia_after")


class TriviaReviewLogViewSet(viewsets.ModelViewSet):
    serializer_class = TriviaReviewLogSerializer
    queryset = TriviaReviewLog.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("trivia", "is_approved_before", "is_approved_after", "edit_status_before", "edit_status_after",
                     "user")
    search_fields = ("trivia__trivia", 'user__username')


class ChannelClipViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelClipSerializer
    queryset = ChannelClip.objects.all().order_by('start_time')
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("channel", "date")
    search_fields = ("channel__channel_name", "video__title")
    action_serializer_classes = {
        "create": CreateChannelClipSerializer,
        "update": CreateChannelClipSerializer,
        "retrieve": ChannelClipSerializer,
    }
    pagination_class = ShortResultsSetPagination

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(ChannelClipViewSet, self).get_serializer_class()

    def retrieve(self, *args, **kwargs):
        retrieve_channelclip_response = super(
            ChannelClipViewSet, self).retrieve(*args, **kwargs)
        retrieve_channelclip_response.data['put_fprint'] = reverse.reverse(
            viewname='video-frame-tags', kwargs=kwargs, request=self.request)
        return retrieve_channelclip_response

    @detail_route(methods=['get'])
    def put_fprint(self, request, pk=None):
        c_clip = self.get_object()
        put_fingerprint.delay(c_clip.id)
        return Response(data={'msg': 'success'}, status=status.HTTP_200_OK)


class BarcChannelsViewSet(viewsets.ModelViewSet):
    serializer_class = BarcChannelSerializer
    # permission_classes = (IsAuthenticated,)
    queryset = Channel.objects.all().filter(channelclip__isnull=False).distinct()
    filter_backends = (filters.SearchFilter,)
    search_fields = ("channel_name",)

    def get_serializer_context(self):
        return {'request': self.request}

    def retrieve(self, *args, **kwargs):
        retrieve_response = super(
            BarcChannelsViewSet, self).retrieve(*args, **kwargs)
        retrieve_response.data['get_report'] = reverse.reverse(viewname='barcchannel-get-report', kwargs=kwargs,
                                                               request=self.request)
        return retrieve_response

    def reset_xml_child(self, obj_arr, value):
        for obj in obj_arr:
            obj.text = value

    def reset_csv_row(self, data_rows, obj_ind, val_ind, value):
        for ind in obj_ind:
            tmp = data_rows[ind]
            tmp[val_ind] = value
            data_rows[ind] = tmp
        return data_rows

    @detail_route(methods=['get'])
    def get_report(self, request, pk=None):
        channel = self.get_object()
        user = request.user
        spec_channel = SpecChannel.objects.filter(
            code=channel.channel_code).first()
        query_params = request.query_params
        date = query_params.get('date', None)
        ext = query_params.get('ext', 'csv')
        send_report.delay(channel.id, date, user.email, ext)
        return Response(data={"message": "success"}, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def load_playouttags(self, request, pk=None):
        channel = self.get_object()
        spec_channel = SpecChannel.objects.filter(
            code=channel.channel_code).first()
        query_params = request.query_params
        date = query_params.get('date', None)
        yr = int(date.split('-')[0])
        mm = int(date.split('-')[1])
        dd = int(date.split('-')[2])
        start_datetime = datetime(
            year=yr, month=mm, day=dd) + timedelta(hours=2)
        end_datetime = datetime(
            year=yr, month=mm, day=dd) + timedelta(hours=26)
        channel_clips = ChannelClip.objects.filter(Q(channel=channel) and Q(
            start_time__gte=start_datetime) and Q(end_time__lt=end_datetime)).order_by('start_time')


class SongVerificationViewSet(viewsets.ModelViewSet):
    """
    Song Verification ViewSet
    """
    serializer_class = SongVerificationSerializer
    queryset = SongVerification.objects.all()
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post']


class AssetVersionViewSet(viewsets.ModelViewSet):
    """
    AssetVersion ViewSet
    """
    serializer_class = AssetVersionSerializer
    queryset = AssetVersion.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    permission_classes = (CustomDjangoModelPermission,)
    filter_fields = ("is_tagged",)
    action_serializer_classes = {
        "create": AssetVersionSerializer,
        "update": AssetVersionSerializer,
        "retrieve": DetailedAssetVersionSerializer,
        "list": DetailedAssetVersionSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(AssetVersionViewSet, self).get_serializer_class()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = AssetVersionSerializer(
            AssetVersion.objects.get(id=serializer.data['id']), )
        return Response(complete_ser.data)

    def update(self, request, *args, **kwargs):
        """
        To cater the full object of foreign keys after update
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = DetailedAssetVersionSerializer(AssetVersion.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)

    # @list_route(methods=['delete'])
    # def delete_multiple(self, request, *args, **kwargs):
    # 	qs = self.get_queryset(*args, **kwargs)
    # 	qs.delete()
        # return Response(status=status.HTTP_204_NO_CONTENT)
    @list_route(methods=['post'])
    def delete_multiple(self, request, uuid=None):
        """
        Overridden method allows either url parameter of single UUID 
        (to delete a single instance), or multiple query parameters `uuids`
        to delete multiple instances.
        """
        if not uuid:
            uuids = request.query_params.get('ids', None)
            uuids = uuids.split(",")
            if not uuids:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if len(uuids) != AssetVersion.objects.filter(id__in=uuids).count():
                return Response(status=status.HTTP_404_NOT_FOUND)
            AssetVersion.objects.filter(id__in=uuids).delete()
        else:
            instance = self.get_object(uuid)
            if not instance:
                return Response(status=status.HTTP_404_NOT_FOUND)
            instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionViewSet(viewsets.ModelViewSet):
    """
    Create New Collection Viewset
    """
    serializer_class = CollectionSerializer
    queryset = Collection.objects.all().order_by('-created_on')
    permission_classes = (CustomDjangoModelPermission,)
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    pagination_class = ShortResultsSetPagination
    search_fields = ("title",)
    filter_fields = ("channel",)
    action_serializer_classes = {
        "create": CollectionSerializer,
        "update": CollectionSerializer,
        "retrieve": DetailedCollectionSerializer,
        "list": DetailedCollectionSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(CollectionViewSet, self).get_serializer_class()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = DetailedCollectionSerializer(Collection.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)


class AssignWorkFlowInstanceStepViewSet(viewsets.ModelViewSet):
    """
    Create Viewset for assigning work flow instance step to a person
    """
    serializer_class = AssignWorkFlowInstanceStepSerializer
    queryset = AssignWorkFlowInstanceStep.objects.all()
    permission_classes = (CustomDjangoModelPermission,)

    # To accomodate multiple object creation with a single request
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class SegmentViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Assigning a segment
    """
    serializer_class = SegmentSerializer
    queryset = Segment.objects.all()
    permission_classes = (IsAuthenticated,)


class RushesViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Assigning Rushes
    """
    serializer_class = DetailedRushesSerializer
    queryset = Rushes.objects.all().order_by('-ingested_on')
    permission_classes = (CustomDjangoContentPermission,)
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    pagination_class = ShortResultsSetPagination
    search_fields = ('title', 'asset_version__title',
                     'asset_version__video__title')
    # filter_fields = ("channel", 'asset_version__assigned__assigned_to')
    filter_class = RushesFilter
    action_serializer_classes = {
        "create": RushesSerializer,
        "update": RushesSerializer,
        "retrieve": DetailedRushesSerializer,
        "list": DetailedRushesSerializer,
        "partial_update": RushesSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(RushesViewSet, self).get_serializer_class()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = DetailedRushesSerializer(Rushes.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)

    @list_route(methods=['get'])
    def library(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_content_by_channel(queryset, request)

        """
		Filter Logic begins
		"""
        genres = request.query_params.get('genre', None)
        if genres:
            genres = genres.split(",")

        dates = request.query_params.get('created_on', None)
        start_date = None
        end_date = None
        if dates:
            start_date = dates.split(",")[0] if dates else None
            end_date = dates.split(",")[1] if dates else None

        ingest_date = request.query_params.get('ingested_on', None)
        ingest_start_date = None
        ingest_end_date = None
        if ingest_date:
            ingest_start_date = ingest_date.split(
                ",")[0] if ingest_date else None
            ingest_end_date = ingest_date.split(
                ",")[1] if ingest_date else None

        channel = request.query_params.get('channel', None)

        is_active = request.query_params.get('is_active', None)
        is_active = None if not is_active else (
            True if is_active and is_active == "true" else False)

        is_tagged = request.query_params.get('is_tagged', None)
        is_tagged = None if not is_tagged else (
            True if is_tagged and is_tagged == "true" else False)

        search = request.query_params.get('search', None)

        kwargs = {
            '{0}__{1}'.format('genre', 'in'): genres,
            '{0}'.format('channel'): channel,
            '{0}__{1}__{2}'.format('created_on', 'date', 'gte'): start_date,
            '{0}__{1}__{2}'.format('created_on', 'date', 'lte'): end_date,
            '{0}__{1}'.format('ingested_on', 'gte'): ingest_start_date,
            '{0}__{1}'.format('ingested_on', 'lte'): ingest_end_date,
        }

        # remove all values having None values
        kwargs_dict = {k: v for k, v in kwargs.items() if v is not None}
        queryset = queryset.filter(**kwargs_dict)

        query = None
        if is_active is not None:
            query = Q(asset_version__proxy_type="SRC") & Q(
                asset_version__is_active=is_active)

        if is_tagged is not None:
            query = Q(asset_version__proxy_type="SRC") & Q(
                asset_version__is_tagged=is_tagged)

        if query != None:
            queryset = queryset.filter(query)

        if search:
            query = (Q(title__iexact=search) | Q(asset_version__title__iexact=search) | Q(
                asset_version__video__title__iexact=search))
            qs = queryset.filter(query)
            if qs.count() == 0:
                query = (Q(title__icontains=search) | Q(asset_version__title__icontains=search) | Q(
                    asset_version__video__title__icontains=search))
                qs = queryset.filter(query)
            queryset = qs

        """
		Filter Logic ends
		"""

        page = self.paginate_queryset(queryset)
        if page is not None:
            asset_list = []
            for asset in page:
                asset_res = CognitiveSearchRushesSerializer(
                    asset, context={'request': request}).data
                query = Q(object_id=asset.id) & Q(proxy_type="SRC")

                if is_active is not None:
                    query &= Q(is_active=is_active)

                if is_tagged is not None:
                    query &= Q(is_tagged=is_tagged)

                asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.all().filter(
                    query).distinct().order_by('-created_on'), many=True, context={'request': request}).data
                asset_res["asset_version"] = asset_version
                asset_list.append(asset_res)
            return self.get_paginated_response(asset_list)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # To accomodate Channel based permissions
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_content_by_channel(queryset, request)

        """
		Filter Logic begins
		"""
        genres = request.query_params.get('genre', None)
        if genres:
            genres = genres.split(",")

        dates = request.query_params.get('created_on', None)
        start_date = None
        end_date = None
        if dates:
            start_date = dates.split(",")[0] if dates else None
            end_date = dates.split(",")[1] if dates else None

        assigned_to = request.query_params.get('assigned_to', None)

        is_assigned = request.query_params.get('is_assigned', None)
        is_assigned = None if not is_assigned else (
            True if is_assigned and is_assigned == "true" else False)

        ingest_date = request.query_params.get('ingested_on', None)
        ingest_start_date = None
        ingest_end_date = None
        if ingest_date:
            ingest_start_date = ingest_date.split(
                ",")[0] if ingest_date else None
            ingest_end_date = ingest_date.split(
                ",")[1] if ingest_date else None

        channel = request.query_params.get('channel', None)

        is_active = request.query_params.get('is_active', None)
        is_active = None if not is_active else (
            True if is_active and is_active == "true" else False)

        is_tagged = request.query_params.get('is_tagged', None)
        is_tagged = None if not is_tagged else (
            True if is_tagged and is_tagged == "true" else False)

        workflow = request.query_params.get('workflow', None)

        search = request.query_params.get('search', None)

        kwargs = {
            '{0}__{1}'.format('genre', 'in'): genres,
            '{0}'.format('channel'): channel,
            '{0}__{1}'.format('asset_version', 'is_tagged'): is_tagged,
            '{0}__{1}'.format('asset_version', 'is_active'): is_active,
            '{0}__{1}__{2}'.format('created_on', 'date', 'gte'): start_date,
            '{0}__{1}__{2}'.format('created_on', 'date', 'lte'): end_date,
            '{0}__{1}'.format('ingested_on', 'gte'): ingest_start_date,
            '{0}__{1}'.format('ingested_on', 'lte'): ingest_end_date,
        }

        # remove all values having None values
        kwargs_dict = {k: v for k, v in kwargs.items() if v is not None}
        queryset = queryset.filter(**kwargs_dict)

        # For Manual Tagging platform which doesnt require workflow integration
        if is_tagged is not None:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        # keep workflow=None condition
        user_all_memberships = WorkGroupMembership.objects.filter(
            user=request.user)
        user_all_workgroups = WorkGroup.objects.filter(
            members__in=user_all_memberships)

        # Show only those assets whose workflow contains my workgroup
        query = None
        if not request.user.is_superuser:
            query = Q(asset_version__work_flow_instances__work_flow=workflow) & Q(
                asset_version__work_flow_instances__work_flow_instance_steps__work_flow_step__workgroup__in=user_all_workgroups)
        else:
            query = Q(asset_version__work_flow_instances__work_flow=workflow)

        if workflow is not None and is_assigned is not None:
            if is_assigned == True:
                query &= Q(
                    asset_version__work_flow_instances__work_flow_instance_steps__assigned__isnull=False)
            else:
                query &= Q(
                    asset_version__work_flow_instances__work_flow_instance_steps__assigned__isnull=True)

        if workflow is not None and assigned_to is not None:
            query &= Q(
                asset_version__work_flow_instances__work_flow_instance_steps__assigned__assigned_to=assigned_to)

        queryset = queryset.filter(query).distinct()

        if search:
            query = (Q(title__iexact=search) | Q(asset_version__title__iexact=search) | Q(
                asset_version__video__title__iexact=search))
            qs = queryset.filter(query)
            if qs.count() == 0:
                query = (Q(title__icontains=search) | Q(asset_version__title__icontains=search) | Q(
                    asset_version__video__title__icontains=search))
                qs = queryset.filter(query)
            queryset = qs

        """
		Filter Logic ends
		"""

        page = self.paginate_queryset(queryset)
        if page is not None:
            asset_list = []
            for asset in page:
                asset_res = CognitiveSearchRushesSerializer(
                    asset, context={'request': request}).data
                query = Q(object_id=asset.id) & Q(
                    work_flow_instances__work_flow=workflow)

                if not request.user.is_superuser:
                    query &= Q(
                        work_flow_instances__work_flow_instance_steps__work_flow_step__workgroup__in=user_all_workgroups)

                if is_active is not None:
                    query &= Q(is_active=is_active)

                if workflow is not None and is_assigned is not None:
                    if is_assigned == True:
                        query &= Q(
                            work_flow_instances__work_flow_instance_steps__assigned__isnull=False)
                    else:
                        query &= Q(
                            work_flow_instances__work_flow_instance_steps__assigned__isnull=True)

                if workflow is not None and assigned_to is not None:
                    query &= Q(
                        work_flow_instances__work_flow_instance_steps__assigned__assigned_to=assigned_to)

                asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.all().filter(
                    query).distinct().order_by('-created_on'), many=True, context={'request': request}).data
                asset_res["asset_version"] = asset_version
                asset_list.append(asset_res)
            return self.get_paginated_response(asset_list)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ContentTypeViewSet(viewsets.ModelViewSet):
    """
    Creating a Viewset for Content Type
    """
    serializer_class = ContentTypeSerializer
    queryset = ContentType.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend,)
    search_fields = ("model",)
    filter_fields = ("app_label",)

    @list_route(methods=['get'])
    def fetchcontenttypes(self, request):
        models = ["promo", "rushes", "series", "songasset",
                  "movie", "commercialasset", "episode"]
        qs = ContentType.objects.all().filter(model__in=models, app_label="content")

        content_type_serializer = ContentTypeSerializer(
            qs, context={"request": request}, many=True)
        return Response(content_type_serializer.data, status=status.HTTP_200_OK)


class MetadataAudioViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Song metadata
    """
    serializer_class = MetadataAudioSerializer
    queryset = MetadataAudio.objects.all()
    permission_classes = (IsAuthenticated,)


class SongAssetViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Song Asset
    """
    serializer_class = DetailedSongAssetSerializer
    queryset = SongAsset.objects.all().order_by('created_on')
    permission_classes = (CustomDjangoContentPermission,)
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    search_fields = ('title', 'asset_version__title',
                     'asset_version__video__title')
    filter_fields = ("channel",)

    action_serializer_classes = {
        "create": SongAssetSerializer,
        "update": SongAssetSerializer,
        "retrieve": DetailedSongAssetSerializer,
        "list": DetailedSongAssetSerializer,
        "partial_update": SongAssetSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(SongAssetViewSet, self).get_serializer_class()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = DetailedSongAssetSerializer(SongAsset.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)

    @list_route(methods=['get'])
    def library(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_content_by_channel(queryset, request)

        """
		Filter Logic begins
		"""
        genres = request.query_params.get('genre', None)
        if genres:
            genres = genres.split(",")

        dates = request.query_params.get('created_on', None)
        start_date = None
        end_date = None
        if dates:
            start_date = dates.split(",")[0] if dates else None
            end_date = dates.split(",")[1] if dates else None

        ingest_date = request.query_params.get('ingested_on', None)
        ingest_start_date = None
        ingest_end_date = None
        if ingest_date:
            ingest_start_date = ingest_date.split(
                ",")[0] if ingest_date else None
            ingest_end_date = ingest_date.split(
                ",")[1] if ingest_date else None

        channel = request.query_params.get('channel', None)

        is_active = request.query_params.get('is_active', None)
        is_active = None if not is_active else (
            True if is_active and is_active == "true" else False)

        is_tagged = request.query_params.get('is_tagged', None)
        is_tagged = None if not is_tagged else (
            True if is_tagged and is_tagged == "true" else False)

        search = request.query_params.get('search', None)

        kwargs = {
            '{0}__{1}'.format('genre', 'in'): genres,
            '{0}'.format('channel'): channel,
            '{0}__{1}__{2}'.format('created_on', 'date', 'gte'): start_date,
            '{0}__{1}__{2}'.format('created_on', 'date', 'lte'): end_date,
            '{0}__{1}'.format('ingested_on', 'gte'): ingest_start_date,
            '{0}__{1}'.format('ingested_on', 'lte'): ingest_end_date,
        }

        # remove all values having None values
        kwargs_dict = {k: v for k, v in kwargs.items() if v is not None}
        queryset = queryset.filter(**kwargs_dict)

        query = None
        if is_active is not None:
            query = Q(asset_version__proxy_type="SRC") & Q(
                asset_version__is_active=is_active)

        if is_tagged is not None:
            query = Q(asset_version__proxy_type="SRC") & Q(
                asset_version__is_tagged=is_tagged)

        if query != None:
            queryset = queryset.filter(query)

        if search:
            query = (Q(title__iexact=search) | Q(asset_version__title__iexact=search) | Q(
                asset_version__video__title__iexact=search))
            qs = queryset.filter(query)
            if qs.count() == 0:
                query = (Q(title__icontains=search) | Q(asset_version__title__icontains=search) | Q(
                    asset_version__video__title__icontains=search))
                qs = queryset.filter(query)
            queryset = qs

        """
		Filter Logic ends
		"""

        page = self.paginate_queryset(queryset)
        if page is not None:
            asset_list = []
            for asset in page:
                asset_res = CognitiveSearchSongAssetSerializer(
                    asset, context={'request': request}).data
                query = Q(object_id=asset.id) & Q(proxy_type="SRC")

                if is_active is not None:
                    query &= Q(is_active=is_active)

                if is_tagged is not None:
                    query &= Q(is_tagged=is_tagged)

                asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.all().filter(
                    query).distinct().order_by('-created_on'), many=True, context={'request': request}).data
                asset_res["asset_version"] = asset_version
                asset_list.append(asset_res)
            return self.get_paginated_response(asset_list)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # To accomodate Channel based permissions
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_content_by_channel(queryset, request)

        """
		Filter Logic begins
		"""
        genres = request.query_params.get('genre', None)
        if genres:
            genres = genres.split(",")

        dates = request.query_params.get('created_on', None)
        start_date = None
        end_date = None
        if dates:
            start_date = dates.split(",")[0] if dates else None
            end_date = dates.split(",")[1] if dates else None

        assigned_to = request.query_params.get('assigned_to', None)

        is_assigned = request.query_params.get('is_assigned', None)
        is_assigned = None if not is_assigned else (
            True if is_assigned and is_assigned == "true" else False)

        ingest_date = request.query_params.get('ingested_on', None)
        ingest_start_date = None
        ingest_end_date = None
        if ingest_date:
            ingest_start_date = ingest_date.split(
                ",")[0] if ingest_date else None
            ingest_end_date = ingest_date.split(
                ",")[1] if ingest_date else None

        channel = request.query_params.get('channel', None)

        is_active = request.query_params.get('is_active', None)
        is_active = None if not is_active else (
            True if is_active and is_active == "true" else False)

        is_tagged = request.query_params.get('is_tagged', None)
        is_tagged = None if not is_tagged else (
            True if is_tagged and is_tagged == "true" else False)

        workflow = request.query_params.get('workflow', None)

        search = request.query_params.get('search', None)

        kwargs = {
            '{0}__{1}'.format('genre', 'in'): genres,
            '{0}'.format('channel'): channel,
            '{0}__{1}'.format('asset_version', 'is_tagged'): is_tagged,
            '{0}__{1}'.format('asset_version', 'is_active'): is_active,
            '{0}__{1}__{2}'.format('created_on', 'date', 'gte'): start_date,
            '{0}__{1}__{2}'.format('created_on', 'date', 'lte'): end_date,
            '{0}__{1}'.format('ingested_on', 'gte'): ingest_start_date,
            '{0}__{1}'.format('ingested_on', 'lte'): ingest_end_date,
        }

        # remove all values having None values
        kwargs_dict = {k: v for k, v in kwargs.items() if v is not None}
        queryset = queryset.filter(**kwargs_dict)

        # For Manual Tagging platform which doesnt require workflow integration
        if is_tagged is not None:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        # keep workflow=None condition
        user_all_memberships = WorkGroupMembership.objects.filter(
            user=request.user)
        user_all_workgroups = WorkGroup.objects.filter(
            members__in=user_all_memberships)

        # Show only those assets whose workflow contains my workgroup
        query = None
        if not request.user.is_superuser:
            query = Q(asset_version__work_flow_instances__work_flow=workflow) & Q(
                asset_version__work_flow_instances__work_flow_instance_steps__work_flow_step__workgroup__in=user_all_workgroups)
        else:
            query = Q(asset_version__work_flow_instances__work_flow=workflow)

        if workflow is not None and is_assigned is not None:
            if is_assigned == True:
                query &= Q(
                    asset_version__work_flow_instances__work_flow_instance_steps__assigned__isnull=False)
            else:
                query &= Q(
                    asset_version__work_flow_instances__work_flow_instance_steps__assigned__isnull=True)

        if workflow is not None and assigned_to is not None:
            query &= Q(
                asset_version__work_flow_instances__work_flow_instance_steps__assigned__assigned_to=assigned_to)

        queryset = queryset.filter(query).distinct()

        if search:
            query = (Q(title__iexact=search) | Q(asset_version__title__iexact=search) | Q(
                asset_version__video__title__iexact=search))
            qs = queryset.filter(query)
            if qs.count() == 0:
                query = (Q(title__icontains=search) | Q(asset_version__title__icontains=search) | Q(
                    asset_version__video__title__icontains=search))
                qs = queryset.filter(query)
            queryset = qs

        """
		Filter Logic ends
		"""

        page = self.paginate_queryset(queryset)
        if page is not None:
            asset_list = []
            for asset in page:
                asset_res = CognitiveSearchSongAssetSerializer(
                    asset, context={'request': request}).data
                query = Q(object_id=asset.id) & Q(
                    work_flow_instances__work_flow=workflow)

                if not request.user.is_superuser:
                    query &= Q(
                        work_flow_instances__work_flow_instance_steps__work_flow_step__workgroup__in=user_all_workgroups)

                if is_active is not None:
                    query &= Q(is_active=is_active)

                if workflow is not None and is_assigned is not None:
                    if is_assigned == True:
                        query &= Q(
                            work_flow_instances__work_flow_instance_steps__assigned__isnull=False)
                    else:
                        query &= Q(
                            work_flow_instances__work_flow_instance_steps__assigned__isnull=True)

                if workflow is not None and assigned_to is not None:
                    query &= Q(
                        work_flow_instances__work_flow_instance_steps__assigned__assigned_to=assigned_to)

                asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.all().filter(
                    query).distinct().order_by('-created_on'), many=True, context={'request': request}).data
                asset_res["asset_version"] = asset_version
                asset_list.append(asset_res)
            return self.get_paginated_response(asset_list)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BatchViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Batch
    """
    serializer_class = BatchSerializer
    queryset = Batch.objects.all()
    permission_classes = (IsAuthenticated,)


class VideoProcessingStatusViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Batch
    """
    serializer_class = VideoProcessingStatusSerializer
    queryset = VideoProcessingStatus.objects.all()
    permission_classes = (IsAuthenticated,)


class AdvancedSearchViewSet(viewsets.ViewSet):

    def list(self, request):
        search_query = request.query_params.get("query", '')
        content_type = request.query_params.get("type", '95')
        content_type = int(content_type)
        ##
        # results = advanced_search(search_query)
        # asset_list = []
        # for result in results.items():
        # 	asset = {}
        # 	assetversion = DetailedAssetVersionSerializer(AssetVersion.objects.all().filter(id=result[0], content_type__id=content_type).first(), context={'request':request})
        # 	asset["asset_version"] = assetversion.data
        # 	asset["search_times"] = result[1]
        # 	asset_list.append(asset)
        ##
        content = ContentType.objects.all().filter(id=content_type).first()
        if content:
            results = advanced_search(search_query, content_type)
            asset_map = {}
            asset_list = []
            index = 0
            for result in results.items():
                asset = None
                # models = ["promo", "rushes", "series", "songasset", "movie", "commercial"]
                if content.model == "promo":
                    asset = CognitiveSearchPromoSerializer(Promo.objects.all().filter(
                        asset_version__id=result[0]).first(), context={'request': request}).data
                    if asset:
                        asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.filter(
                            id=result[0]).first(), context={'request': request}).data
                        asset_version["search_times"] = result[1]
                        if asset["id"] in asset_map:
                            index = asset_map[asset["id"]]
                            asset_list[index][
                                "asset_version"].append(asset_version)
                        else:
                            asset_map[asset["id"]] = index
                            asset["asset_version"] = []
                            asset["asset_version"].append(asset_version)
                            asset_list.append(asset)
                            index += 1
                elif content.model == "rushes":
                    asset = CognitiveSearchRushesSerializer(Rushes.objects.all().filter(
                        asset_version__id=result[0]).first(), context={'request': request}).data
                    if asset:
                        asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.filter(
                            id=result[0]).first(), context={'request': request}).data
                        asset_version["search_times"] = result[1]
                        if asset["id"] in asset_map:
                            index = asset_map[asset["id"]]
                            asset_list[index][
                                "asset_version"].append(asset_version)
                        else:
                            asset_map[asset["id"]] = index
                            asset["asset_version"] = []
                            asset["asset_version"].append(asset_version)
                            asset_list.append(asset)
                            index += 1
                elif content.model == "songasset":
                    asset = CognitiveSearchSongAssetSerializer(SongAsset.objects.all().filter(
                        asset_version__id=result[0]).first(), context={'request': request}).data
                    if asset:
                        asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.filter(
                            id=result[0]).first(), context={'request': request}).data
                        asset_version["search_times"] = result[1]
                        if asset["id"] in asset_map:
                            index = asset_map[asset["id"]]
                            asset_list[index][
                                "asset_version"].append(asset_version)
                        else:
                            asset_map[asset["id"]] = index
                            asset["asset_version"] = []
                            asset["asset_version"].append(asset_version)
                            asset_list.append(asset)
                            index += 1
                elif content.model == "movie":
                    asset = CognitiveSearchMovieSerializer(Movie.objects.all().filter(
                        asset_version__id=result[0]).first(), context={'request': request}).data
                    if asset:
                        asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.filter(
                            id=result[0]).first(), context={'request': request}).data
                        asset_version["search_times"] = result[1]
                        if asset["id"] in asset_map:
                            index = asset_map[asset["id"]]
                            asset_list[index][
                                "asset_version"].append(asset_version)
                        else:
                            asset_map[asset["id"]] = index
                            asset["asset_version"] = []
                            asset["asset_version"].append(asset_version)
                            asset_list.append(asset)
                            index += 1
                elif content.model == "commercialasset":
                    asset = CognitiveSearchCommercialAssetSerializer(CommercialAsset.objects.all(
                    ).filter(asset_version__id=result[0]).first(), context={'request': request}).data
                    if asset:
                        asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.filter(
                            id=result[0]).first(), context={'request': request}).data
                        asset_version["search_times"] = result[1]
                        if asset["id"] in asset_map:
                            index = asset_map[asset["id"]]
                            asset_list[index][
                                "asset_version"].append(asset_version)
                        else:
                            asset_map[asset["id"]] = index
                            asset["asset_version"] = []
                            asset["asset_version"].append(asset_version)
                            asset_list.append(asset)
                            index += 1
                elif content.model == "series":
                    series = CognitiveSearchSeriesSerializer(Series.objects.all().filter(
                        seasons__episodes__asset_version__id=result[0]).first(), context={'request': request}).data
                    season = CognitiveSearchSeasonSerializer(Season.objects.all().filter(
                        episodes__asset_version__id=result[0]).first(), context={'request': request}).data
                    episode = CognitiveSearchEpisodeSerializer(Episode.objects.all().filter(
                        asset_version__id=result[0]).first(), context={'request': request}).data
                    asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.filter(
                        id=result[0]).first(), context={'request': request}).data
                    asset_version["search_times"] = result[1]
                    if series["id"] in asset_map:
                        series = asset_map[series["id"]]
                        index = series["index"]
                        season_map = series["season_map"]
                        season_index = len(season_map)
                        if season["id"] in season_map:
                            season = season_map[season["id"]]
                            season_index = season["index"]
                            episode_map = season["episode_map"]
                            episode_index = len(episode_map)
                            if episode["id"] in episode_map:
                                episode = episode_map[episode["id"]]
                                episode_index = episode["index"]
                                asset_list[index]["seasons"][season_index]["episodes"][
                                    episode_index]["asset_version"].append(asset_version)
                            else:
                                asset_map[series["id"]][season_map][season["id"]][
                                    episode_map][episode["id"]]["index"] = episode_index
                                episode["asset_version"] = []
                                episode["asset_version"].append(asset_version)
                                asset_list[index]["seasons"][
                                    season_index].append(episode)
                                episode_index += 1
                        else:
                            asset_map[series["id"]][season_map][
                                season["id"]]["index"] = season_index
                            season["episodes"] = []
                            season["episodes"].append(episode)
                            asset_list[index].append(season)
                            season_index += 1
                    else:
                        asset_map[series["id"]]["index"] = index
                        series["seasons"] = []
                        series["seasons"].append(season)
                        asset_list.append(series)
                        index += 1
        else:
            Response(data={"message": "Error in data"},
                     status=status.HTTP_400_BAD_REQUEST)
        return Response(data={"results": asset_list}, status=status.HTTP_200_OK)


class SequenceViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Sequence
    """
    serializer_class = SequenceSerializer
    queryset = Sequence.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    pagination_class = ShortResultsSetPagination
    search_fields = ("asset_version",)
    filter_fields = ("asset_version",)
    permission_classes = (CustomDjangoModelPermission,)


class WorkFlowViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Sequence
    """
    serializer_class = WorkFlowSerializer
    queryset = WorkFlow.objects.all()
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    search_fields = ('title',)
    permission_classes = (
        CustomDjangoModelPermission,
        IsAuthenticated,
        UserAccessModelPermission
    )
    action_serializer_classes = {
        "create": WorkFlowSerializer,
        "update": WorkFlowSerializer,
        "retrieve": WorkFlowSerializer,
        "list": DetailedWorkFlowSerializer,
    }

    def get_queryset(self):
        checker = ObjectPermissionChecker(self.request.user)
        workflows_id = [w.id for w in WorkFlow.objects.all() if checker.has_perm('user_view_workflow', w) or checker.has_perm('org_view_workflow', w) or checker.has_perm('team_view_workflow', w)]
        return WorkFlow.objects.filter(id__in=workflows_id)

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(WorkFlowViewSet, self).get_serializer_class()


class WorkFlowStepViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Sequence
    """
    serializer_class = WorkFlowStepSerializer
    queryset = WorkFlowStep.objects.all()
    permission_classes = (
        CustomDjangoModelPermission,
        IsAuthenticated
    )


class WorkFlowInstanceViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Sequence
    """
    serializer_class = WorkFlowInstanceSerializer
    queryset = WorkFlowInstance.objects.all()
    permission_classes = (
        CustomDjangoModelPermission,
        IsAuthenticated,
        UserAccessModelPermission
    )
    action_serializer_classes = {
        "create": WorkFlowInstanceSerializer,
        "update": WorkFlowInstanceSerializer,
        "retrieve": DetailedWorkFlowInstanceSerializer,
        "list": DetailedWorkFlowInstanceSerializer,
    }

    def get_queryset(self):
        checker = ObjectPermissionChecker(self.request.user)
        wid = [w.id for w in WorkFlowInstance.objects.all() if checker.has_perm('user_view_project', w) or checker.has_perm('org_view_project', w) or checker.has_perm('team_view_project', w)]
        return WorkFlowInstance.objects.filter(id__in=projects_id)

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(WorkFlowInstanceViewSet, self).get_serializer_class()

    # To accomodate multiple object creation with a single request
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class WorkFlowInstanceStepViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Sequence
    """
    serializer_class = WorkFlowInstanceStepSerializer
    queryset = WorkFlowInstanceStep.objects.all().order_by("created_on")
    permission_classes = (
        CustomDjangoModelPermission,
        IsAuthenticated
    )


class WorkFlowCollectionInstanceViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Sequence
    """
    serializer_class = WorkFlowCollectionInstanceSerializer
    queryset = WorkFlowCollectionInstance.objects.all()
    permission_classes = (
        CustomDjangoModelPermission,
        IsAuthenticated
    )
    action_serializer_classes = {
        "create": WorkFlowCollectionInstanceSerializer,
        "update": WorkFlowCollectionInstanceSerializer,
        "retrieve": DetailedWorkFlowCollectionInstanceSerializer,
        "list": DetailedWorkFlowCollectionInstanceSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(WorkFlowCollectionInstanceViewSet, self).get_serializer_class()

    # To accomodate multiple object creation with a single request
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class WorkFlowCollectionInstanceStepViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Sequence
    """
    serializer_class = WorkFlowCollectionInstanceStepSerializer
    queryset = WorkFlowCollectionInstanceStep.objects.all().order_by("created_on")
    permission_classes = (
        CustomDjangoModelPermission,
        IsAuthenticated
    )


class AssignWorkFlowCollectionInstanceStepViewSet(viewsets.ModelViewSet):
    """
    Create Viewset for assigning work flow instance step to a person
    """
    serializer_class = AssignWorkFlowCollectionInstanceStepSerializer
    queryset = AssignWorkFlowCollectionInstanceStep.objects.all()
    permission_classes = (IsAuthenticated,)

    # To accomodate multiple object creation with a single request
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class WorkFlowStageViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Sequence
    """
    serializer_class = WorkFlowStageSerializer
    queryset = WorkFlowStage.objects.all()
    permission_classes = (
        CustomDjangoModelPermission,
        IsAuthenticated
    )
    action_serializer_classes = {
        "create": WorkFlowStageSerializer,
        "list": DetailedWorkFlowStageSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(WorkFlowStageViewSet, self).get_serializer_class()


class WorkFlowTransitionHistoryViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Sequence
    """
    serializer_class = WorkFlowTransitionHistorySerializer
    queryset = WorkFlowTransitionHistory.objects.all()
    permission_classes = (
        CustomDjangoModelPermission,
        IsAuthenticated
    )


class CommercialAssetViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset for Commercial
    """
    serializer_class = DetailedCommercialAssetSerializer
    queryset = CommercialAsset.objects.all()
    permission_classes = (IsAuthenticated,)
    action_serializer_classes = {
        "create": CommercialAssetSerializer,
        "update": CommercialAssetSerializer,
        "retrieve": DetailedCommercialAssetSerializer,
        "list": DetailedCommercialAssetSerializer,
        "partial_update": CommercialAssetSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(CommercialAssetSerializer, self).get_serializer_class()

    # #To accomodate Channel based permissions
    # def list(self, request, *args, **kwargs):
    # 	queryset = self.filter_queryset(self.get_queryset())
    # 	queryset = filter_content_by_channel(queryset, request)

    # 	page = self.paginate_queryset(queryset)
    # 	if page is not None:
    # 		serializer = self.get_serializer(page, many=True)
    # 		return self.get_paginated_response(serializer.data)

    # 	serializer = self.get_serializer(queryset, many=True)
    # 	return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = DetailedCommercialAssetSerializer(CommercialAsset.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)

    @list_route(methods=['get'])
    def library(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_content_by_channel(queryset, request)

        """
		Filter Logic begins
		"""
        genres = request.query_params.get('genre', None)
        if genres:
            genres = genres.split(",")

        dates = request.query_params.get('created_on', None)
        start_date = None
        end_date = None
        if dates:
            start_date = dates.split(",")[0] if dates else None
            end_date = dates.split(",")[1] if dates else None

        ingest_date = request.query_params.get('ingested_on', None)
        ingest_start_date = None
        ingest_end_date = None
        if ingest_date:
            ingest_start_date = ingest_date.split(
                ",")[0] if ingest_date else None
            ingest_end_date = ingest_date.split(
                ",")[1] if ingest_date else None

        channel = request.query_params.get('channel', None)

        is_active = request.query_params.get('is_active', None)
        is_active = None if not is_active else (
            True if is_active and is_active == "true" else False)

        is_tagged = request.query_params.get('is_tagged', None)
        is_tagged = None if not is_tagged else (
            True if is_tagged and is_tagged == "true" else False)

        search = request.query_params.get('search', None)

        kwargs = {
            '{0}__{1}'.format('genre', 'in'): genres,
            '{0}'.format('channel'): channel,
            '{0}__{1}__{2}'.format('created_on', 'date', 'gte'): start_date,
            '{0}__{1}__{2}'.format('created_on', 'date', 'lte'): end_date,
            '{0}__{1}'.format('ingested_on', 'gte'): ingest_start_date,
            '{0}__{1}'.format('ingested_on', 'lte'): ingest_end_date,
        }

        # remove all values having None values
        kwargs_dict = {k: v for k, v in kwargs.items() if v is not None}
        queryset = queryset.filter(**kwargs_dict)

        query = None
        if is_active is not None:
            query = Q(asset_version__proxy_type="SRC") & Q(
                asset_version__is_active=is_active)

        if is_tagged is not None:
            query = Q(asset_version__proxy_type="SRC") & Q(
                asset_version__is_tagged=is_tagged)

        if query != None:
            queryset = queryset.filter(query)

        if search:
            query = (Q(title__iexact=search) | Q(asset_version__title__iexact=search) | Q(
                asset_version__video__title__iexact=search))
            qs = queryset.filter(query)
            if qs.count() == 0:
                query = (Q(title__icontains=search) | Q(asset_version__title__icontains=search) | Q(
                    asset_version__video__title__icontains=search))
                qs = queryset.filter(query)
            queryset = qs

        """
		Filter Logic ends
		"""

        page = self.paginate_queryset(queryset)
        if page is not None:
            asset_list = []
            for asset in page:
                asset_res = CognitiveSearchCommercialAssetSerializer(
                    asset, context={'request': request}).data
                query = Q(object_id=asset.id) & Q(proxy_type="SRC")

                if is_active is not None:
                    query &= Q(is_active=is_active)

                if is_tagged is not None:
                    query &= Q(is_tagged=is_tagged)

                asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.all().filter(
                    query).distinct().order_by('-created_on'), many=True, context={'request': request}).data
                asset_res["asset_version"] = asset_version
                asset_list.append(asset_res)
            return self.get_paginated_response(asset_list)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # To accomodate Channel based permissions
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_content_by_channel(queryset, request)

        """
		Filter Logic begins
		"""
        genres = request.query_params.get('genre', None)
        if genres:
            genres = genres.split(",")

        dates = request.query_params.get('created_on', None)
        start_date = None
        end_date = None
        if dates:
            start_date = dates.split(",")[0] if dates else None
            end_date = dates.split(",")[1] if dates else None

        assigned_to = request.query_params.get('assigned_to', None)

        is_assigned = request.query_params.get('is_assigned', None)
        is_assigned = None if not is_assigned else (
            True if is_assigned and is_assigned == "true" else False)

        ingest_date = request.query_params.get('ingested_on', None)
        ingest_start_date = None
        ingest_end_date = None
        if ingest_date:
            ingest_start_date = ingest_date.split(
                ",")[0] if ingest_date else None
            ingest_end_date = ingest_date.split(
                ",")[1] if ingest_date else None

        channel = request.query_params.get('channel', None)

        is_active = request.query_params.get('is_active', None)
        is_active = None if not is_active else (
            True if is_active and is_active == "true" else False)

        is_tagged = request.query_params.get('is_tagged', None)
        is_tagged = None if not is_tagged else (
            True if is_tagged and is_tagged == "true" else False)

        workflow = request.query_params.get('workflow', None)

        search = request.query_params.get('search', None)

        kwargs = {
            '{0}__{1}'.format('genre', 'in'): genres,
            '{0}'.format('channel'): channel,
            '{0}__{1}'.format('asset_version', 'is_tagged'): is_tagged,
            '{0}__{1}'.format('asset_version', 'is_active'): is_active,
            '{0}__{1}__{2}'.format('created_on', 'date', 'gte'): start_date,
            '{0}__{1}__{2}'.format('created_on', 'date', 'lte'): end_date,
            '{0}__{1}'.format('ingested_on', 'gte'): ingest_start_date,
            '{0}__{1}'.format('ingested_on', 'lte'): ingest_end_date,
        }

        # remove all values having None values
        kwargs_dict = {k: v for k, v in kwargs.items() if v is not None}
        queryset = queryset.filter(**kwargs_dict)

        # For Manual Tagging platform which doesnt require workflow integration
        if is_tagged is not None:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        # keep workflow=None condition
        user_all_memberships = WorkGroupMembership.objects.filter(
            user=request.user)
        user_all_workgroups = WorkGroup.objects.filter(
            members__in=user_all_memberships)

        # Show only those assets whose workflow contains my workgroup
        query = None
        if not request.user.is_superuser:
            query = Q(asset_version__work_flow_instances__work_flow=workflow) & Q(
                asset_version__work_flow_instances__work_flow_instance_steps__work_flow_step__workgroup__in=user_all_workgroups)
        else:
            query = Q(asset_version__work_flow_instances__work_flow=workflow)

        if workflow is not None and is_assigned is not None:
            if is_assigned == True:
                query &= Q(
                    asset_version__work_flow_instances__work_flow_instance_steps__assigned__isnull=False)
            else:
                query &= Q(
                    asset_version__work_flow_instances__work_flow_instance_steps__assigned__isnull=True)

        if workflow is not None and assigned_to is not None:
            query &= Q(
                asset_version__work_flow_instances__work_flow_instance_steps__assigned__assigned_to=assigned_to)

        queryset = queryset.filter(query).distinct()

        if search:
            query = (Q(title__iexact=search) | Q(asset_version__title__iexact=search) | Q(
                asset_version__video__title__iexact=search))
            qs = queryset.filter(query)
            if qs.count() == 0:
                query = (Q(title__icontains=search) | Q(asset_version__title__icontains=search) | Q(
                    asset_version__video__title__icontains=search))
                qs = queryset.filter(query)
            queryset = qs

        """
		Filter Logic ends
		"""

        page = self.paginate_queryset(queryset)
        if page is not None:
            asset_list = []
            for asset in page:
                asset_res = CognitiveSearchCommercialAssetSerializer(
                    asset, context={'request': request}).data
                query = Q(object_id=asset.id) & Q(
                    work_flow_instances__work_flow=workflow)

                if not request.user.is_superuser:
                    query &= Q(
                        work_flow_instances__work_flow_instance_steps__work_flow_step__workgroup__in=user_all_workgroups)

                if is_active is not None:
                    query &= Q(is_active=is_active)

                if workflow is not None and is_assigned is not None:
                    if is_assigned == True:
                        query &= Q(
                            work_flow_instances__work_flow_instance_steps__assigned__isnull=False)
                    else:
                        query &= Q(
                            work_flow_instances__work_flow_instance_steps__assigned__isnull=True)

                if workflow is not None and assigned_to is not None:
                    query &= Q(
                        work_flow_instances__work_flow_instance_steps__assigned__assigned_to=assigned_to)

                asset_version = DetailedAssetVersionSerializer(AssetVersion.objects.all().filter(
                    query).distinct().order_by('-created_on'), many=True, context={'request': request}).data
                asset_res["asset_version"] = asset_version
                asset_list.append(asset_res)
            return self.get_paginated_response(asset_list)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DemoViewSet(viewsets.ModelViewSet):
    """
    Creating Viewset For Website Demo
    """
    serializer_class = DemoSerializer
    queryset = Demo.objects.all()
    permission_classes = (AllowAny,)

    @list_route(methods=['post'])
    def resetpass(self, request):
        uid = request.data.get("start_date",None)
        password = request.data.get("password", None)
        user = DemoOTP.objects.filter(uniq_id=uid)[0]
        user.password = password
        user.save()
        return Response(data={"created": "True"}, status=status.HTTP_200_OK)

class DemoViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """
    Creates, Updates, and retrieves Demo User accounts
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    action_serializer_classes = {
        "create": CreateUserSerializer,
    }
    permission_classes = (AllowAny, )
   
    def get_queryset(self):
        return User.objects.all()

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(DemoViewSet, self).get_serializer_class()



class CategoriesViewset(viewsets.ModelViewSet):
    """
    Creating Viewset for folder categories
    """
    serializer_class = CategoriesSerializer
    queryset = Folder.objects.filter(parent__isnull=True)
    permission_classes = (IsAuthenticated,)
    action_serializer_classes = {
        "create": NewCategoriesSerializer,
        "update": NewCategoriesSerializer,
        "retrieve": CategoriesSerializer,
        "list": CategoriesSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(CategoriesSerializer, self).get_serializer_class()

class FolderViewSet(viewsets.ModelViewSet):
    action_serializer_classes = {
        "create": NewFolderSerializer,
        "update": NewFolderSerializer,
        "list": FolderSerializer
    }
    queryset = Folder.objects.all()
    permission_classes = (IsAuthenticated, UserAccessModelPermission)

    def get_queryset(self):
        channel = self.request.query_params.get('channel', '')
        category = self.request.query_params.get('category', '')
        parent = self.request.query_params.get('parent', '')
        id = self.request.query_params.get('id', '')
        dates = self.request.query_params.get('created_on', None)
        search = self.request.query_params.get('search', '')
        sort = self.request.query_params.get('sort', '')
        start_date = None
        end_date = None
        if dates:
            start_date = dates.split(",")[0] if dates else None
            end_date = dates.split(",")[1] if dates else None
        qs = Folder.objects.all()

        if sort:
            qs = qs.reverse()
        if search:
            f = File.objects.filter(title__icontains=search).values('location')
            files = qs.filter(id__in=f)
            folders = qs.filter(title__icontains=search)
            qs = (files | folders)

        if id:
            qs = qs.filter(id=id)
        if channel:
            qs = qs.filter(channel__channel_name=channel)
        if category:
            qs = qs.filter(category=category)
        if parent:
            qs = qs.objects.filter(parent=parent)
        if dates:
            qs.filter(created_on__gte=start_date, created_on__lte=end_date)
        return qs

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return FolderSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                "search": self.request.query_params.get('search')
            }
        )
        return context

    @list_route(methods=['post'])
    def delete_multiple(self, request, uuid=None):
        """
        Overridden method allows either url parameter of single UUID 
        (to delete a single instance), or multiple query parameters `uuids`
        to delete multiple instances.
        """
        if not uuid:
            uuids = request.query_params.get('ids', None)
            uuids = uuids.split(",")
            if not uuids:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if len(uuids) != Folder.objects.filter(id__in=uuids).count():
                return Response(status=status.HTTP_404_NOT_FOUND)
            Folder.objects.filter(id__in=uuids).delete()
            return Response({"id":uuids}, status=status.HTTP_200_OK)
        else:
            instance = self.get_object(uuid)
            if not instance:
                return Response(status=status.HTTP_404_NOT_FOUND)
            instance.delete()
            return Response({"id":uuid}, status=status.HTTP_200_OK)


class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    queryset = File.objects.all()
    permission_classes = (IsAuthenticated, UserAccessModelPermission)

    action_serializer_classes = {
        "create": NewFileSerializer,
        "retrieve": FileSerializer,
        "list": FileSerializer,
        # "update": CreateFileSerializer
    }

    def get_queryset(self):
        search = self.request.query_params.get('search', '')
        channel = self.request.query_params.get('channel', '')
        type = self.request.query_params.get('type', '')
        qs = File.objects.all()
        if channel:
            qs = qs.filter(channel=channel)
        if search:
            qs = qs.filter(title__icontains = search)
        return qs

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        print(datetime.now().time())
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(FileViewSet, self).get_serializer_class()

    @list_route(methods=['post'])
    def delete_multiple(self, request, uuid=None):
        """
        Overridden method allows either url parameter of single UUID 
        (to delete a single instance), or multiple query parameters `uuids`
        to delete multiple instances.
        """
        if not uuid:
            uuids = request.query_params.get('ids', None)
            uuids = uuids.split(",")
            if not uuids:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if len(uuids) != Folder.objects.filter(id__in=uuids).count():
                return Response(status=status.HTTP_404_NOT_FOUND)
            Folder.objects.filter(id__in=uuids).delete()
            return Response({"id":uuids}, status=status.HTTP_200_OK)
        else:
            instance = self.get_object(uuid)
            if not instance:
                return Response(status=status.HTTP_404_NOT_FOUND)
            instance.delete()
            return Response({"id":uuid}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def search_metadata(self, request, pk=None):
        file = self.get_object()
        search = request.query_params.get("name", "")
        result_set = []
        for value in file.file_metadata.values():
            for k, v in value.items():
                if search != None and (search in str(k).lower() or search in str(v).lower()):
                    result_set.append({k: v})
        return Response({'results': result_set}, status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes((JSONParser,)) 
def aws_uploadid(request, format=None):
    try:
        print(request.data)
        client = boto3.client('s3')
        mupload = client.create_multipart_upload( ACL='bucket-owner-full-control',
                                        Key = request.data["fileName"],
                                        Bucket = 'trigger-uploaded-videos')
        upload_id = mupload["UploadId"]
        return Response(data={
                "UploadId": upload_id,
            }, status=status.HTTP_200_OK)
    except ClientError as e:
        print(e)
        print(e.message)
        return Response(data={
                "Error": e.message,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@parser_classes((JSONParser,)) 
def aws_presigned_url(request, format=None):
    try:
        client = boto3.client('s3')
        data = request.data
        print(data)
        file_name = data["fileName"]
        upload_id = data["UploadId"]
        parts = data["parts"]
        res = []
        for i in range(parts):
            url = client.generate_presigned_url(ClientMethod='upload_part',
                                            Params={'Bucket': 'trigger-uploaded-videos',
                                                    'Key': file_name,
                                                    'UploadId': upload_id,
                                                    'PartNumber': i+1})
            res.append(url)
        return Response(data={
                "result": res,
            }, status=status.HTTP_200_OK)
    except ClientError as e:
        return Response(data={
                "Error": e,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@parser_classes((JSONParser,)) 
def aws_complete(request, format=None):
    try:
        client = boto3.client('s3')
        data = request.data
        folder_id = data["folderId"]
        file_name = data["fileName"]
        upload_id = data["UploadId"]
        file_type = data['type']
        channel_name = data['channel']
        parts = data["parts"]
        res = client.complete_multipart_upload(Bucket = 'trigger-uploaded-videos',
                                            Key = file_name,
                                            UploadId = upload_id,
                                            MultipartUpload = { 'Parts': parts })
        channel = Channel.objects.filter(channel_name=channel_name).first()
        folder_obj = Folder.objects.get(pk=folder_id)
        file = File.objects.create(title=file_name, location=folder_obj, type=file_type, url=res['Location'], channel=channel)
        user = request.user
        assign_perm('view_file', user, file)
        assign_perm('change_file', user, file)
        assign_perm('delete_file', user, file)
        return Response(data={
                "result": res,
            }, status=status.HTTP_200_OK)
    except ClientError as e:
        print(e)
        print(e.message)
        return Response(data={
                "Error": e,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def library(request):
    search = request.GET.get("search", None)
    dates = request.GET.get('created_on', None)
    file_type = request.GET.get('file_type', None)
    parent = request.GET.get('parent', None)
    channel = request.GET.get('channel', None)
    category = request.GET.get('category', None)
    order_by = request.GET.get('order_by', None)
    start_date = None
    end_date = None

    if dates:
        start_date = dates.split(",")[0] if dates else None
        end_date = dates.split(",")[1] if dates else None

    checker = ObjectPermissionChecker(request.user)
    folders_id = [f.id for f in Folder.objects.all() if checker.has_perm('user_view_folder', f) or checker.has_perm('org_view_folder', f) or checker.has_perm('team_view_folder', f)]
    files_id = [f.id for f in File.objects.all() if checker.has_perm('user_view_file', f) or checker.has_perm('org_view_file', f) or checker.has_perm('team_view_file', f)]
    folders = Folder.objects.filter(id__in=folders_id)
    files = File.objects.filter(id__in=files_id)

    if search:
        files = files.filter(title__icontains=search)
        folders = folders.filter(title__icontains=search)

    if parent:
        folders = folders.filter(parent=parent)
        files = files.filter(location=parent)

    if dates:
        files = files.filter(created_on__gte=start_date, created_on__lte=end_date)
        folders = folders.filter(created_on__gte=start_date, created_on__lte=end_date)

    if category:
        category = category.split(",")
        folders = folders.filter(category__in=category)
        files = files.filter(category__in=category)

    if channel:
        files = files.filter(channel__id=channel)
        folders = folders.filter(channel__id=channel)

    if file_type:
        file_type = file_type.split(",")
        files = files.filter(type__in=file_type)
        folders = Folder.objects.none()

    contents = list(chain(set(files) | set(folders)))
    contents = sorted(contents, key=lambda x: x.created_on)

    if order_by:
        if order_by == "descending":
            contents.reverse()

    results = []
    for content in contents:
        content_type = content.__class__.__name__.lower()
        if isinstance(content, Folder):
            ser = ContentsSerializer(content)
        if isinstance(content, File):
            ser = FileSerializer(content)
        results.append({"type": content_type, "data": ser.data})
    if parent:
        f = Folder.objects.get(pk=parent)
        parents = get_parent_folders(f)
        return Response(data={
            "id": f.id,
            "title": f.title,
            "result": results,
            "parent_folders": parents
        }, status=status.HTTP_200_OK)
    return Response(data={
        "result": results
    }, status=status.HTTP_200_OK)

def get_parent_folders(obj):
    if obj.parent is None:
        return []
    folder_list = get_parent_folders(obj.parent)
    parent = obj.parent
    folder_list.append({parent.title: parent.id})
    return folder_list

@api_view(['GET'])
def librarysearch(request, format=None):
    search = request.GET["search"]
    dates = request.GET.get('created_on', None)
    file_type = request.GET.get('file_type', None)
    parent = request.GET.get('parent', None)
    category = request.GET.get('category', None)
    order_by = request.GET.get('order_by', None)
    start_date = None
    end_date = None

    if dates:
        start_date = dates.split(",")[0] if dates else None
        end_date = dates.split(",")[1] if dates else None

    files = File.objects.filter(title__icontains=search)
    folders = Folder.objects.filter(title__icontains=search)

    if dates:
        files = files.filter(created_on__gte=start_date, created_on__lte=end_date)
        folders = folders.filter(created_on__gte=start_date, created_on__lte=end_date)

    if file_type:
        file_type = file_type.split(",")
        files = files.filter(type__in=file_type)
    if category:
        category = category.split(",")
        folders = folders.filter(category__in=category)
    if parent:
        folders = folders.filter(parent=parent)
        files = files.filter(location=parent)

    contents = list(chain(set(files) | set(folders)))
    contents = sorted(contents, key=lambda x: x.created_on)

    if order_by:
        if order_by == "descending":
            contents.reverse()

    results = []
    for content in contents:
        content_type = content.__class__.__name__.lower()
        if isinstance(content, Folder):
            ser = ContentsSerializer(content)
        if isinstance(content, File):
            ser = FileSerializer(content)
        results.append({"type": content_type, "data": ser.data})
    return Response(data={
        "result": results
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def library_delete(request, uuid=None):
    """
    Overridden method allows either url parameter of single UUID
    (to delete a single instance), or multiple query parameters `uuids`
    to delete multiple instances.
    """
    uuids = request.data.get('ids', None)
    if not uuids:
        return Response(status=status.HTTP_404_NOT_FOUND)
    deleted = []
    for uuid in uuids:
        if uuid["type"] == "file":
            try:
                File.objects.get(pk=uuid["id"]).delete()
                deleted.append(uuid["id"])
            except:
                return Response(data={"result":"invalid id"}, status=status.HTTP_400_BAD_REQUEST)
        elif uuid["type"] == "folder":
            try:
                Folder.objects.get(pk=uuid["id"]).delete()
                deleted.append(uuid["id"])
            except:
                return Response(data={"result":"invalid id"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data={"result":"invalid object type"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"id":deleted}, status=status.HTTP_200_OK)

@api_view(['GET'])
def generate_report(request, format=None):
    search = request.GET["search"]
    dates = request.GET.get('created_on', None)
    file_type = request.GET.get('file_type', None)
    category = request.GET.get('category', None)
    results = librarysearch(request).data.get('result', None)
    if results:
        response = HttpResponse('text/csv')
        response['Content-Disposition'] = 'attachment; filename=search_report.csv'
        writer = csv.writer(response)
        writer.writerow(["Search query", search])
        writer.writerow(["Date range", dates])
        if file_type:
            writer.writerow(["File type", *file_type.split(",")])
        if category:
            writer.writerow(["Category", *category.split(",")])

        writer.writerow(["type", "id", "title"])
        for result in results:
            writer.writerow([result["type"], result["data"]["id"], result["data"]["title"]])
        return response

@api_view(['POST'])
@parser_classes((JSONParser,))
def reset_password(request, format=None):
    password = request.data.get("password", None)
    token = request.data.get("token", None)



class ProjectViewset(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    queryset = Projects.objects.all()
    permission_classes = (IsAuthenticated, UserAccessModelPermission)

    action_serializer_classes = {
        "create": ProjectSerializer,
        "retrieve": DetailedProjectSerializer,
        "list": DetailedProjectSerializer,
        "update": ProjectSerializer,
    }
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    search_fields = ('name',)
    filter_fields = ('workflow',)
    filter_class = ProjectFilter

    def get_queryset(self):
        checker = ObjectPermissionChecker(self.request.user)
        projects_id = [p.id for p in Projects.objects.all() if checker.has_perm('user_view_projects', p) or checker.has_perm('org_view_projects', p) or checker.has_perm('team_view_projects', p)]
        return Projects.objects.filter(id__in=projects_id)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        project_version = ProjectVersion.objects.filter(project=instance).order_by("-created_on").first()
        if request.data['workflow'] and project_version.workflow_instance is None:
            workflow = WorkFlow.objects.get(id=request.data['workflow'])         
            workflow_instance = WorkFlowInstance.objects.create(work_flow=workflow)
            project_version.workflow_instance = workflow_instance
            project_version.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = DetailedProjectSerializer(Projects.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return DetailedProjectSerializer

class ProjectVersionViewset(viewsets.ModelViewSet):
    serializer_class = ProjectVersionSerializer
    queryset = ProjectVersion.objects.all()
    permission_classes = (IsAuthenticated, UserAccessModelPermission)

    action_serializer_classes = {
        "create": CreateProjectVersionSerializer,
        "retrieve": ProjectVersionSerializer,
        "list": ProjectVersionSerializer,
        "update": CreateProjectVersionSerializer
    }

    def get_queryset(self):
        checker = ObjectPermissionChecker(self.request.user)
        projects_id = [p.id for p in ProjectVersion.objects.all() if checker.has_perm('user_view_projectversion', p) or checker.has_perm('org_view_projectversion', p) or checker.has_perm('team_view_projectversion', p)]
        return ProjectVersion.objects.filter(id__in=projects_id)

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return ProjectVersionSerializer

class ProjectFileViewset(viewsets.ModelViewSet):
    serializer_class = ProjectFileSerializer
    queryset = ProjectFiles.objects.all()
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('project',)
    

    action_serializer_classes = {
        "create": ProjectFileSerializer,
        "retrieve": DetailedProjectFileSerializer,
        "list": DetailedProjectFileSerializer,
        "update": ProjectFileSerializer
    }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(ProjectFileSerializer, self).get_serializer_class()


class ProjectMetadataViewset(viewsets.ModelViewSet):
    serializer_class = ProjectMetadataSerializer
    queryset = ProjectMetadata.objects.all()
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('project',)


    action_serializer_classes = {
        "create": ProjectMetadataSerializer,
        "retrieve": DetailedProjectMetadataSerializer,
        "list": DetailedProjectMetadataSerializer,
        "update": ProjectMetadataSerializer
    }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        for data in serializer.data:
            data['workflow_metadata'] = WorkFlowMetadataSerializer(WorkFlowMetadata.objects.get(id=data['workflow_metadata'])).data
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = DetailedProjectMetadataSerializer(ProjectMetadata.objects.get(
            id=serializer.data['id']), context={'request': request})
        return Response(complete_ser.data)

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return ProjectMetadataSerializer


class WorkFlowMetadataViewset(viewsets.ModelViewSet):
    serializer_class = WorkFlowMetadataSerializer
    queryset = WorkFlowMetadata.objects.all()
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('workflow',)

    action_serializer_classes = {
        "create": WorkFlowMetadataSerializer,
        "retrieve": WorkFlowMetadataSerializer,
        "list": WorkFlowMetadataSerializer,
        "update": WorkFlowMetadataSerializer
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(WorkFlowMetadataSerializer, self).get_serializer_class()
