#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from rest_framework import (
    viewsets,
    reverse
)
from rest_framework.decorators import detail_route, list_route
from rest_framework import filters
import django_filters
from .models import (
    TaggingJob,
    JobType,
    FrameJob,
    AutoVideoJob,
    SubtitleSyncJob,
    ScriptProcessJob,
    SubtitleTranslationJob,
    ReviewTranslationJob,
    MovieTranslationJob,
    EpisodeTranslationJob
)
from .tasks import subtitle_sync, script_process

from .serializers import (
    TaggingJobSerializer,
    CreateTaggingJobSerializer,
    JobTypeSerializer,
    FrameJobSerializer,
    AutoVideoJobSerializer,
    CreateAutoVideoJobSerializer,
    SubtitleSyncJobSerializer,
    DetailSubtitleSyncJobSerializer,
    ScriptProcessJobSerializer,
    CreateSubtitleTranslationJobSerializer,
    DetailSubtitleTranslationJobSerializer,
    ListSubtitleTranslationJobSerializer,
    CreateReviewTranslationJobSerializer,
    DetailReviewTranslationJobSerializer,
    ListReviewTranslationJobSerializer,
    UpdateReviewTranslationJobSerializer,
    DetailMovieTranslationJobSerializer,
    UpdateMovieTranslationJobSerializer,
    CreateMovieTranslationJobSerializer,
    DetailEpisodeTranslationJobSerializer,
    UpdateEpisodeTranslationJobSerializer,
    CreateEpisodeTranslationJobSerializer

)

from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated


class JobTypeViewSet(viewsets.ModelViewSet):
    serializer_class = JobTypeSerializer
    queryset = JobType.objects.all()


class TaggingJobViewSet(viewsets.ModelViewSet):
    serializer_class = TaggingJobSerializer
    queryset = TaggingJob.objects.all()
    action_serializer_classes = {
        "create": CreateTaggingJobSerializer,
        "retrieve": CreateTaggingJobSerializer,
    }

    def get_queryset(self):
        return TaggingJob.objects.all().filter(Q(taken_by = self.request.user)| Q(created_by = self.request.user))

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(TaggingJobViewSet, self).get_serializer_class()


class AutoVideoJobViewSet(viewsets.ModelViewSet):
    serializer_class = AutoVideoJobSerializer
    queryset = AutoVideoJob.objects.all()
    action_serializer_classes = {
        "create": CreateAutoVideoJobSerializer,
        "retrieve": AutoVideoJobSerializer,
    }

    def get_queryset(self):
        search = self.request.query_params.get("search", None)
        j = AutoVideoJob.objects.all()
        if search:
            j = j.filter(video__id=search)
        return j

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(AutoVideoJobViewSet, self).get_serializer_class()


class FrameJobViewSet(viewsets.ModelViewSet):
    serializer_class = FrameJobSerializer

    def get_queryset(self):
        return FrameJob.objects.all().filter(Q(assigned_to = self.request.user)| Q(created_by = self.request.user))


class SubtitleSyncJobViewSet(viewsets.ModelViewSet):
    serializer_class = SubtitleSyncJobSerializer
    action_serializer_classes = {
        "retrieve": DetailSubtitleSyncJobSerializer,
    }

    def get_queryset(self):
        return SubtitleSyncJob.objects.all().filter(created_by=self.request.user)

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(SubtitleSyncJobViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['created_by'] = str(self.request.user.id)
        serializer = self.get_serializer(data=data, )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, *args, **kwargs):
        retrieve_sub_sync_response = super(SubtitleSyncJobViewSet, self).retrieve(*args, **kwargs)
        retrieve_sub_sync_response.data['process_for_sync'] = reverse.reverse(viewname='subtitlesyncjob-process-for-sync',
                                                                              kwargs=kwargs,
                                                                              request=self.request)
        return retrieve_sub_sync_response

    @detail_route(methods=['get'])
    def process_for_sync(self, request, pk=None):
        audio_instance = self.get_object()
        subtitle_sync.delay(audio_instance.id)
        return Response({"status":"process started"}, status=status.HTTP_200_OK)


class ScriptProcessViewSet(viewsets.ModelViewSet):
    serializer_class = ScriptProcessJobSerializer

    def get_queryset(self):
        return ScriptProcessJob.objects.all().filter(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['created_by'] = str(self.request.user.id)
        serializer = self.get_serializer(data=data, )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, *args, **kwargs):
        retrieve_script_process_response = super(ScriptProcessViewSet, self).retrieve(*args, **kwargs)
        retrieve_script_process_response.data['process_for_text'] = reverse.reverse(viewname='scriptprocessjob-process-for-text',
                                                                              kwargs=kwargs,
                                                                              request=self.request)
        return retrieve_script_process_response

    @detail_route(methods=['get'])
    def process_for_text(self, request, pk=None):
        script_instance = self.get_object()
        script_process.delay(script_instance.id)
        return Response({"status ": "process started"}, status=status.HTTP_200_OK)


class SubtitleTranslationJobViewSet(viewsets.ModelViewSet):
    serializer_class = ListSubtitleTranslationJobSerializer
    action_serializer_classes = {
        "create": CreateSubtitleTranslationJobSerializer,
        "retrieve": DetailSubtitleTranslationJobSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(SubtitleTranslationJobViewSet, self).get_serializer_class()

    def get_queryset(self):
        return SubtitleTranslationJob.objects.all().filter(Q(created_by=self.request.user)|Q(assigned_to=self.request.user))

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['created_by'] = str(self.request.user.id)
        serializer = self.get_serializer(data=data, )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['get'])
    def assigned_to(self, request):
        qs = SubtitleTranslationJob.objects.all().filter(assigned_to=request.user)
        serializer = ListSubtitleTranslationJobSerializer(qs, context={'request': request}, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    @list_route(methods=['get'])
    def created_by(self, request):
        qs = SubtitleTranslationJob.objects.all().filter(created_by=request.user)
        serializer = ListSubtitleTranslationJobSerializer(qs, context={'request': request}, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)


class ReviewTranslationJobViewSet(viewsets.ModelViewSet):
    serializer_class = ListReviewTranslationJobSerializer
    action_serializer_classes = {
        "create": CreateReviewTranslationJobSerializer,
        "retrieve": DetailReviewTranslationJobSerializer,
        "update": UpdateReviewTranslationJobSerializer
    }
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    search_fields = ('video__title',)
    filter_fields = ('priority', 'target_language', 'job_status')
    ordering_fields = ('created_on', 'priority', 'due_date', 'modified_on')

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(ReviewTranslationJobViewSet, self).get_serializer_class()

    def get_queryset(self):
        return ReviewTranslationJob.objects.all().filter(Q(created_by=self.request.user)|Q(assigned_to=self.request.user))

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['created_by'] = str(self.request.user.id)
        serializer = self.get_serializer(data=data, )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['get'])
    def assigned_to(self, request):
        qs = ReviewTranslationJob.objects.all().filter(assigned_to=request.user)
        serializer = ListReviewTranslationJobSerializer(qs, context={'request': request}, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    @list_route(methods=['get'])
    def created_by(self, request):
        qs = ReviewTranslationJob.objects.all().filter(created_by=request.user)
        serializer = ListReviewTranslationJobSerializer(qs, context={'request': request}, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)


class MovieTranslationJobViewSet(viewsets.ModelViewSet):
    serializer_class = DetailMovieTranslationJobSerializer
    action_serializer_classes = {
        "create": CreateMovieTranslationJobSerializer,
        "retrieve": DetailMovieTranslationJobSerializer,
        "update": UpdateMovieTranslationJobSerializer
    }
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('priority', 'target_language', 'job_status', 'assigned_to')
    search_fields = ('movie__movie_title',)
    ordering_fields = ('created_on', 'priority', 'due_date', 'modified_on')

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(MovieTranslationJobViewSet, self).get_serializer_class()

    def get_queryset(self):
        queryset = MovieTranslationJob.objects.all().filter(Q(created_by=self.request.user)|Q(assigned_to=self.request.user))
        queryset = queryset.select_related('movie_segment', 'movie', 'created_by', 'assigned_to')
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['created_by'] = str(self.request.user.id)
        serializer = self.get_serializer(data=data, )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['get'])
    def assigned_to(self, request):
        qs = MovieTranslationJob.objects.all().filter(assigned_to=request.user)
        serializer = DetailMovieTranslationJobSerializer(qs, context={'request': request}, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    @list_route(methods=['get'])
    def created_by(self, request):
        qs = MovieTranslationJob.objects.all().filter(created_by=request.user)
        serializer = DetailMovieTranslationJobSerializer(qs, context={'request': request}, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)


class EpisodeTranslationJobViewSet(viewsets.ModelViewSet):
    serializer_class = DetailEpisodeTranslationJobSerializer
    action_serializer_classes = {
        "create": CreateEpisodeTranslationJobSerializer,
        "retrieve": DetailEpisodeTranslationJobSerializer,
        "update": UpdateEpisodeTranslationJobSerializer
    }
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
    filters.OrderingFilter)
    filter_fields = ('priority', 'target_language', 'job_status', "assigned_to")
    search_fields = ('episode__episode_title', 'episode__series__series_title')
    ordering_fields = ('created_on', 'priority', 'due_date', 'modified_on')

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(EpisodeTranslationJobViewSet, self).get_serializer_class()

    def get_queryset(self):
        queryset = EpisodeTranslationJob.objects.all().filter(Q(created_by=self.request.user)|Q(assigned_to=self.request.user))
        queryset = queryset.select_related('episode_segment', 'episode', 'created_by', 'assigned_to')
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['created_by'] = str(self.request.user.id)
        serializer = self.get_serializer(data=data, )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @list_route(methods=['get'])
    def assigned_to(self, request):
        qs = EpisodeTranslationJob.objects.all().filter(assigned_to=request.user)
        serializer = DetailMovieTranslationJobSerializer(qs, context={'request': request}, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    @list_route(methods=['get'])
    def created_by(self, request):
        qs = EpisodeTranslationJob.objects.all().filter(created_by=request.user)
        serializer = DetailMovieTranslationJobSerializer(qs, context={'request': request}, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
