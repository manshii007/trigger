#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from rest_framework import serializers
from guardian.shortcuts import assign_perm
from versatileimagefield.serializers import VersatileImageFieldSerializer
from django.db.models import Q
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

# from tags.serializers import (
#     FrameTagSerializer,
#     KeywordTagSerializer,
#     ComplianceStatusSerializer,

# )
from tags.models import (
    ComplianceStatusTag
)
from jobs.models import (
    AutoVideoJob
)
from thumbnails.serializers import (
    ThumbnailSerializer
)
from thumbnails.models import(
    Thumbnail
)

class CreateVideoSerializer(serializers.ModelSerializer):
    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True,
        required=False
    )

    def create(self, validated_data):
        video = Video.objects.create(**validated_data)
        user = self.context['request'].user
        assign_perm('view_video', user, video)
        return video

    class Meta:
        model = Video
        fields = ('id', 'title', 'file', 'poster', 'created_by', 'metadata')
        read_only_fields = ('id',)
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}


class DetailVideoSerializer(serializers.ModelSerializer):

    poster = VersatileImageFieldSerializer(
        sizes='video_poster'
    )
    # frame_tags = FrameTagSerializer(many=True, read_only=True)
    created_on = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ('id', 'title', 'poster', 'created_on', 'duration', 'height', 'width', 'total_frames',
                  'frame_rate', 'file', 'is_removed', 'is_nft') #, 'frame_tags'
        read_only_fields = ('id', 'file')

    def get_created_on(self, obj):
        return obj.created_on.date().strftime("%d-%m-%y")


class AutoVideoJobSerializer(serializers.ModelSerializer):
    job_type = serializers.SlugField(source='job_type.name')

    class Meta:
        model = AutoVideoJob
        fields = ('id', 'created_on', 'modified_on', 'due_date', 'job_status', 'priority', 'created_by',
                  'video', 'job_type', 'eta')

class VideoProxyPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoProxyPath
        fields = "__all__"

class VideoSerializer(serializers.ModelSerializer):
    poster = VersatileImageFieldSerializer(
        sizes='video_poster'
    )
    length = serializers.CharField(source='_readable_duration')
    latest_process = serializers.SerializerMethodField()
    latest_process_status = serializers.HyperlinkedIdentityField(view_name="video-latest-process-status", read_only=True)
    compliance_status = serializers.SerializerMethodField()
    format = serializers.SerializerMethodField()
    metadata = VideoProxyPathSerializer(read_only=True)
    thumbnails = serializers.SerializerMethodField()
    class Meta:
        model = Video
        fields = ('url', 'id', 'title', 'length', 'poster', 'file', 'frame_rate', 'total_frames', 'height', 'width',
                  'duration', 'bitrate', 'video_codec', 'size', 'created_on', 'latest_process_status', "latest_process", "compliance_status", "format", "metadata", 'picture', 'thumbnails', 'is_nft')
        read_only_fields = ('id', 'file')

    def get_format(self, obj):
        if obj.file:
            return obj.file.split(".")[-1]
        return None

    def get_compliance_status(self, obj):
        try:
            go = ComplianceStatusTag.objects.get(video=obj)
            return go.is_approved
        except ComplianceStatusTag.DoesNotExist:
            go = None
            return 'RIV'

    def get_latest_process(self, obj):
        auto_video_job_serializer = AutoVideoJobSerializer(AutoVideoJob.objects.all().filter(video=obj)
                                                           .order_by("job_type", "-created_on").distinct("job_type"),
                                                           context=self.context, many=True)
        return auto_video_job_serializer.data

    def get_thumbnails(self, obj):
        thumbnailserializer = ThumbnailSerializer(Thumbnail.objects.filter(thumbnail=obj),
                                                    context=self.context, many=True)
        return  thumbnailserializer.data

class SearchVideoSerializer(serializers.ModelSerializer):
    match=serializers.SerializerMethodField(required=False)
    title_highlight = serializers.CharField(max_length=128, required=False)
    active_keywords = serializers.SerializerMethodField()
    active_frame_tags = serializers.SerializerMethodField()
    # active_face_groups = serializers.SerializerMethodField()
    class Meta:
        model = Video
        fields = ("id", "url", "title", "title_highlight", "poster", 'created_on', 'duration', 'height', 'width', 'total_frames', 'file', 'match', 'active_keywords', 'active_frame_tags')
        read_only_fields = ("id", "url", "title", "title_highlight", "poster", 'created_on', 'duration', 'height', 'width', 'total_frames', 'file', 'match', 'active_keywords', 'active_frame_tags', 'is_nft' )

    def get_match(self, obj):
        if hasattr(obj, 'match'):
            if obj.match:
                return obj.match.split("...")
            else:
                return []
        else:
            return []

    def get_active_keywords(self, obj):
        if self.context['request'].query_params.get('audio'):
            audio_search_term = self.context['request'].query_params.get('audio').lower()
            keywords_filter_queries = [Q(words__contains=term)|Q(words__contains=term.capitalize()) for term in audio_search_term.split(' ')]
            keywords_filter_query = keywords_filter_queries.pop()
            for item in keywords_filter_queries:
                keywords_filter_query |= item
            filtered_keywords = obj.keywords.all().filter(keywords_filter_query)
            # serializer = KeywordTagSerializer(filtered_keywords, many=True, context={"request":self.context['request']})
            return serializer.data
        else:
            return []

    # def get_active_face_groups(self, obj):
    #     visual_search_term = self.context['request'].query_params.get('visual').lower()
    #     face_groups_filter_queries = [Q(person__name__contains=term)|Q(person__name__contains=term.capitalize()) for term in visual_search_term.split(' ')]
    #     face_groups_filter_query = face_groups_filter_queries.pop()
    #     for item in face_groups_filter_queries:
    #         face_groups_filter_query |= item
    #     serializer = FaceGroupSerializer(FaceGroup.objects.all().filter(video=obj), context=self.context, many=True)
    #     return serializer.data

    def get_active_frame_tags(self, obj):
        if self.context['request'].query_params.get('visual'):
            visual_search_term = self.context['request'].query_params.get('visual').lower()
            frame_tags_filter_queries = [Q(tag__name__contains=term)|Q(tag__name__contains=term.capitalize()) for term in visual_search_term.split(' ')]
            frame_tags_filter_query = frame_tags_filter_queries.pop()
            for item in frame_tags_filter_queries:
                frame_tags_filter_query |= item
            # serializer = FrameTagSerializer(obj.frametag.all().filter(frame_tags_filter_query), context=self.context, many=True, read_only=True)
            return serializer.data
        else:
            return []


class SearchVideoWithoutMatchSerializer(serializers.ModelSerializer):
    title_highlight = serializers.CharField(max_length=128, required=False)

    class Meta:
        model = Video
        fields = ("id", "url", "title", "title_highlight", "poster", 'created_on', 'duration',)
        read_only_fields = ("id", "url", "title", "title_highlight", "poster", 'created_on', 'duration', 'is_nft')


class VideoLibrarySerializer(serializers.ModelSerializer):
    videos = VideoSerializer(many=True)

    class Meta:
        model = VideoLibrary
        fields = ("id", "videos")


class AudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audio
        fields = ("id", "file", "created_on", "modified_on", "duration", "audio_codec")
        read_only_fields = ("id", "created_on", "modified_on", "duration", "audio_codec")


class TranscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcription
        fields = ('id', 'file', 'created_on', 'modified_on')
        read_only_fields = ('id', 'created_on', 'modified_on')


class SubtitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtitle
        fields = ('id', 'file', 'created_on', 'modified_on', 'language', 'asset_version')
        read_only_fields = ('id', 'created_on')


class VideoSubtitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoSubtitle
        fields = ('id', 'url', 'title','subtitle', 'video', 'created_on', 'modified_on')


class CreateVideoSubtitleSerializer(serializers.Serializer):
    file = serializers.URLField()
    language = serializers.CharField(max_length=2)
    video = serializers.UUIDField()
    title = serializers.CharField(max_length=128)

    def create(self, validated_data):
        file = validated_data.get("file")
        language = validated_data.get("language")
        video = validated_data.get("video")
        title = validated_data.get("title")
        subtitle_obj = Subtitle.objects.create({"file":file, "language":language})
        video_subtitle_obj = VideoSubtitle.objects.create({"subtitle":subtitle_obj.id, "video":video, "title":title})
        return video_subtitle_obj


class DetailVideoSubtitleSerializer(serializers.ModelSerializer):
    subtitle = SubtitleSerializer()
    video = VideoSerializer()

    class Meta:
        model = VideoSubtitle
        fields = ('id', 'url', 'title','subtitle', 'video', 'created_on', 'modified_on')

class TicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = "__all__"

class ClipSerializer(serializers.ModelSerializer):
    # ticket = TicketSerializer()
    # video_proxy_path = VideoProxyPathSerializer()
    class Meta:
        model = Clip
        fields = ('id', 'clip_ref', 'status', 'created_on', 'modified_on', 'ticket', 'video_proxy_path')

