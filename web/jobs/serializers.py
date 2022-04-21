#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

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

from video.serializers import DetailVideoSerializer, VideoSerializer
from tags.serializers import MildTagSerializer
from content.serializers import (
    MovieSegmentSerializer,
    EpisodeSegmentSerializer,
    ChannelSerializer,
    SeriesSerializer
)
from content.models import (
    Movie,
    Episode
)

class JobTypeSerializer(ModelSerializer):
    class Meta:
        model = JobType
        fields = '__all__'


class TaggingJobSerializer(ModelSerializer):
    assigned_to = serializers.SlugField(source='assigned_to.name')
    created_in = serializers.SlugField(source='created_in.name')
    job_type = serializers.SlugField(source='job_type.name')
    video = DetailVideoSerializer()

    class Meta:
        model = TaggingJob
        fields = ('id', 'created_on', 'modified_on', 'due_date', 'job_status', 'priority', 'assigned_to', 'created_in',
                  'video', 'job_type')


class CreateTaggingJobSerializer(ModelSerializer):
    class Meta:
        model = TaggingJob
        fields = '__all__'


class TaggingJobAssignmentSerializer(serializers.Serializer):
    video_id = serializers.UUIDField()
    job_type_id = serializers.UUIDField()
    workgroup_id = serializers.UUIDField()


class AutoVideoJobSerializer(serializers.ModelSerializer):
    job_type = serializers.SlugField(source='job_type.name')
    video = DetailVideoSerializer()

    class Meta:
        model = AutoVideoJob
        fields = ('url', 'id', 'created_on', 'modified_on', 'due_date', 'job_status', 'priority', 'created_by',
                  'video', 'job_type', 'eta')


class CreateAutoVideoJobSerializer(serializers.ModelSerializer):
    # job_type = serializers.SlugField(source='job_type.name')

    class Meta:
        model = AutoVideoJob
        fields = ('due_date', 'job_status', 'priority', 'created_by',
                  'video', 'job_type',)
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}

class WorkgroupTaggingJobSerializer(ModelSerializer):
    video = DetailVideoSerializer()

    class Meta:
        model = TaggingJob
        fields = ('url', 'video', 'taken_by', 'job_status')


class FrameJobSerializer(ModelSerializer):
    tags = MildTagSerializer(many=True)

    class Meta:
        model = FrameJob
        fields = ('id', 'created_on', 'modified_on', 'due_date', 'job_status', 'priority', 'assigned_to',
                  'frame', 'tags')


class SubtitleSyncJobSerializer(ModelSerializer):

    class Meta:
        model = SubtitleSyncJob
        fields = ('id', 'url', 'created_on', 'modified_on', 'due_date', 'job_status', 'priority',
                  'audio_file', 'srt_file', 'created_by', 'transcription', 'percent_complete', 'eta')
        read_only_fields = ('id', 'url', 'srt_file')


class DetailSubtitleSyncJobSerializer(ModelSerializer):
    class Meta:
        model = SubtitleSyncJob
        fields = ('id', 'url', 'created_on', 'modified_on', 'due_date', 'job_status', 'priority',
                  'audio_file', 'srt_file', 'created_by', 'transcription', 'percent_complete', 'eta')
        read_only_fields = ('id', 'url', 'srt_file')


class ScriptProcessJobSerializer(ModelSerializer):
    class Meta:
        model = ScriptProcessJob
        fields = ('id', 'url', 'created_on', 'modified_on', 'due_date', 'job_status', 'priority',
                  'script_file', 'txt_file', 'created_by', 'percent_complete', 'eta')
        read_only_fields = ('id', 'url', 'txt_file')


class ListSubtitleTranslationJobSerializer(serializers.HyperlinkedModelSerializer):
    video = DetailVideoSerializer()
    created_by = serializers.SlugField()
    assigned_to = serializers.SlugField()
    class Meta:
        model = SubtitleTranslationJob
        fields = ("id", "url", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'video', 'created_by', 'assigned_to', "source_subtitle", "target_language")
        read_only_fields = ("id", 'url', 'created_on', "modified_on")


class DetailSubtitleTranslationJobSerializer(ModelSerializer):
    video = DetailVideoSerializer()
    created_by = serializers.SlugField()
    assigned_to = serializers.SlugField()

    class Meta:
        model = SubtitleTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'video', 'created_by', 'assigned_to', "source_subtitle", "target_language")
        read_only_fields = ("id", 'created_on', "modified_on")


class CreateSubtitleTranslationJobSerializer(ModelSerializer):

    class Meta:
        model = SubtitleTranslationJob
        fields = ("due_date", "priority", "video", "created_by", "assigned_to", "source_subtitle", "target_language")


class ListReviewTranslationJobSerializer(serializers.ModelSerializer):
    video = DetailVideoSerializer()
    # created_by = serializers.UUIDField()
    # assigned_to = serializers.UUIDField()

    class Meta:
        model = ReviewTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'video', 'created_by', 'assigned_to', "source_subtitle", "target_subtitle", "target_language")
        read_only_fields = ("id", 'created_on', "modified_on")


class DetailReviewTranslationJobSerializer(ModelSerializer):
    video = DetailVideoSerializer()
    # created_by = serializers.SlugField()
    # assigned_to = serializers.SlugField()
    class Meta:
        model = ReviewTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'video', 'created_by', 'assigned_to', "source_subtitle", "target_subtitle", "target_language")
        read_only_fields = ("id", 'created_on', "modified_on")


class CreateReviewTranslationJobSerializer(ModelSerializer):

    class Meta:
        model = ReviewTranslationJob
        fields = ("due_date", "priority", "video", "created_by", "assigned_to", "source_subtitle", "target_subtitle", "target_language")


class UpdateReviewTranslationJobSerializer(ModelSerializer):
    class Meta:
        model = ReviewTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'video', 'created_by', 'assigned_to', "source_subtitle", "target_subtitle", "target_language")
        read_only_fields = ("id", 'created_on', "modified_on", "video", 'created_by')


class MovieSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    class Meta:
        model = Movie
        fields = ("id", "movie_title", 'secondary_title', "short_title", "year_of_release", "language", "genre",
                  "content_subject", "content_synopsis", "characters", "created_on", "modified_on",  "channel")
        read_only_fields = ("id",)


class DetailMovieTranslationJobSerializer(ModelSerializer):
    movie = MovieSerializer()
    movie_segment = MovieSegmentSerializer()

    class Meta:
        model = MovieTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'movie', 'movie_segment', 'created_by', 'assigned_to', "source_subtitle", "target_subtitle", "target_language")
        read_only_fields = ("id", 'created_on', "modified_on")


class CreateMovieTranslationJobSerializer(ModelSerializer):

    class Meta:
        model = MovieTranslationJob
        fields = ("due_date", "priority", "movie", "movie_segment", "created_by", "assigned_to", "source_subtitle", "target_subtitle", "target_language")


class UpdateMovieTranslationJobSerializer(ModelSerializer):
    class Meta:
        model = MovieTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'movie', "movie_segment", 'created_by', 'assigned_to', "source_subtitle", "target_subtitle", "target_language")
        read_only_fields = ("id", 'created_on', "modified_on", "movie", 'created_by')


class EpisodeSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    series = SeriesSerializer(read_only=True)

    class Meta:
        model = Episode
        fields = ("id", "episode_title", "secondary_title", "short_title", "series", "episode_number", "telecast_date",
                  "language", "channel", "content_type", "genre", "content_subject", "content_synopsis", "characters",
                  "set_in_location", "created_on", "modified_on")


class DetailEpisodeTranslationJobSerializer(ModelSerializer):
    episode = EpisodeSerializer()
    episode_segment = EpisodeSegmentSerializer()

    class Meta:
        model = MovieTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'episode', 'episode_segment', 'created_by', 'assigned_to', "source_subtitle", "target_subtitle",
                  "target_language")
        read_only_fields = ("id", 'created_on', "modified_on")


class CreateEpisodeTranslationJobSerializer(ModelSerializer):

    class Meta:
        model = EpisodeTranslationJob
        fields = ("due_date", "priority", "episode", "episode_segment", "created_by", "assigned_to", "source_subtitle",
                  "target_subtitle", "target_language")


class UpdateEpisodeTranslationJobSerializer(ModelSerializer):
    class Meta:
        model = EpisodeTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'episode', "episode_segment", 'created_by', 'assigned_to', "source_subtitle",
                  "target_subtitle", "target_language")
        read_only_fields = ("id", 'created_on', "modified_on", "episode", 'created_by')
