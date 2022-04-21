#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from itertools import chain
from pyexpat import model
from rest_framework import serializers
from django.db.models import Q, F
from versatileimagefield.serializers import VersatileImageFieldSerializer
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm, ObjectPermissionChecker
import traceback

from .models import (
    File,
    Folder,
    ProjectMetadata,
    WorkFlowInstanceMembership,
    PersonGroup,
    CloudPerson,
    Character,
    Episode,
    TriviaEditLog,
    EpisodeSegment,
    Series,
    Person,
    Genre,
    ContextType,
    Channel,
    Politician,
    TVAnchor,
    Actor,
    Movie,
    MovieSegment,
    Trivia,
    Song,
    PlaylistEntry,
    Playlist,
    TriviaLog,
    Label,
    NxSong,
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
    WorkFlow,
    WorkFlowMetadata,
    WorkFlowStep,
    WorkFlowInstance,
    WorkFlowInstanceStep,
    WorkFlowStage,
    WorkFlowTransitionHistory,
    MetadataAudio,
    SongAsset,
    Batch,
    VideoProcessingStatus,
    Sequence,
    Season,
    CommercialAsset,
    WorkFlowCollectionInstance,
    WorkFlowCollectionInstanceStep,
    AssignWorkFlowCollectionInstanceStep,
    Demo,
    ProjectFiles,
    Projects,
    ProjectVersion
)
from frames.serializers import PersonFrameSerializer
from video.serializers import (
    VideoSerializer,
)
from video.models import Video
from jobs.models import (
    MovieTranslationJob,
    EpisodeTranslationJob
)
from comments.models import Comment
from workgroups.models import WorkGroup, Team, Group
from tags.models import Tag, TagCategory, BarcTag, PlayoutTag, FrameTag
from tags.serializers import ContentLanguageSerializer, ProductionHouseSerializer
from users.models import User
from datetime import datetime, timedelta
from rest_framework.serializers import raise_errors_on_nested_writes
from rest_framework.utils import model_meta
import logging
import time

logger = logging.getLogger('debug')


class WorkGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkGroup
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name',)


class ChannelSerializer(serializers.ModelSerializer):
    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True,
    )

    class Meta:
        model = Channel
        fields = ("id", "channel_name", "channel_code",
                  "parent_company", "poster")


class PersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Person
        fields = "__all__"
        read_only_fields = ("id",)


class ActorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Actor
        fields = ("id", "awards", "active_from", "active_till")


class DetailActorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Actor
        fields = "__all__"


class CreatePoliticianWithoutPersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Politician
        fields = "__all__"
        read_only_fields = ("id", "person")


class DetailPersonSerializer(serializers.ModelSerializer):
    personframes = PersonFrameSerializer(read_only=True, many=True)
    actor = ActorSerializer(read_only=True)
    politician = CreatePoliticianWithoutPersonSerializer(read_only=True)
    trivia_count = serializers.SerializerMethodField(read_only=True)
    trivia_stat = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Person
        fields = ("id", "url", "name", "dob", "born_location", "current_location", "description", "father_name",
                  "mother_name", "partner_name", "religion", "caste", "education", "occupation", "picture",
                  "personframes", "actor", "politician", "trivia_count", "trivia_stat", "charatcer_played")
        read_only_fields = ("id", "url",)

    def get_trivia_count(self, obj):
        return Trivia.objects.filter(persons=obj).count()

    def get_trivia_stat(self, obj):
        res = {}
        res['approved'] = Trivia.objects.filter(
            Q(persons=obj) & Q(edit_status='ACP')).count()
        res['disapproved'] = Trivia.objects.filter(
            Q(persons=obj) & Q(edit_status='NCP')).count()
        res['new'] = Trivia.objects.filter(
            Q(persons=obj) & Q(edit_status="CLN")).count()
        res['rewritten'] = Trivia.objects.filter(persons=obj).exclude(
            trivia=F("original_description")).count()
        res['rewritten_new'] = Trivia.objects.filter(Q(persons=obj) & (Q(is_approved='no') | Q(
            is_approved="false"))).exclude(trivia=F("original_description")).count()
        return res


class CharacterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Character
        fields = "__all__"


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = "__all__"


class ContextTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContextType
        fields = "__all__"


class SeriesSerializer(serializers.ModelSerializer):
    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )

    class Meta:
        model = Series
        fields = ("id", "title", "alternate_title", "short_title", "version", "part", "rating", "year_of_release",
                  "number_of_episodes", "poster", "cbfc", "status", "remark", "producers", "actors",
                  "directors", "dop",)


class CreateEpisodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Episode
        fields = "__all__"


class PoliticianSerializer(serializers.ModelSerializer):
    person = DetailPersonSerializer(required=False)
    created_by = serializers.SlugField()

    class Meta:
        model = Politician
        fields = ("id", "url", "description", "political_party", "constituency",
                  "positions", "person", 'created_on', "modified_on", "created_by")
        read_only_fields = ("id", "url", "created_on",
                            "modified_on", "created_by")


class CreatePoliticianSerializer(serializers.ModelSerializer):

    class Meta:
        model = Politician
        fields = "__all__"
        read_only_fields = ("id",)
        extra_kwargs = {'created_by': {
            'default': serializers.CurrentUserDefault(), "read_only": True}}


class PoliticiansByDate(serializers.Serializer):
    date_created = serializers.DateField()
    created_count = serializers.IntegerField()


class PoliticiansByUser(serializers.Serializer):
    date_created = serializers.DateField()
    created_count = serializers.IntegerField()
    creator = serializers.SerializerMethodField()

    def get_creator(self, obj):
        created_by = obj['created_by']
        if created_by is None:
            return "null"
        else:
            user_obj = User.objects.filter(id=created_by).first()
            return user_obj.__str__()


class PoliticiansByDateUser(serializers.Serializer):
    date = serializers.DateField()
    data_list = PoliticiansByUser(many=True)


class TVAnchorSerializer(serializers.ModelSerializer):
    person = DetailPersonSerializer(required=False)

    class Meta:
        model = TVAnchor
        fields = ("id", "url", "books", "organizations", "notable_credits", "awards", "person", 'created_on',
                  "modified_on")
        read_only_fields = ("id", "url", "created_on", "modified_on")


class CreateTVAnchorSerializer(serializers.ModelSerializer):

    class Meta:
        model = TVAnchor
        fields = "__all__"
        read_only_fields = ("id",)


class CreateEpisodeSegmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = EpisodeSegment
        fields = '__all__'
        read_only_fields = ("id",)


class EpisodeSegmentSerializer(serializers.ModelSerializer):
    video = VideoSerializer(read_only=True)

    class Meta:
        model = EpisodeSegment
        fields = '__all__'
        read_only_fields = ("id",)


class DetailEpisodeTranslationJobSerializer(serializers.ModelSerializer):
    episode_segment = EpisodeSegmentSerializer()
    created_by = UserSerializer(many=False, read_only=True)
    assigned_to = UserSerializer(many=False, read_only=True)

    class Meta:
        model = EpisodeTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'episode', 'episode_segment', 'created_by', 'assigned_to', "source_subtitle", "target_subtitle",
                  "target_language")
        read_only_fields = ("id", 'created_on', "modified_on")


class SimpleEpisodeSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    episodesegment_set = EpisodeSegmentSerializer(many=True, read_only=True)
    episodetranslationjob_set = DetailEpisodeTranslationJobSerializer(
        many=True, read_only=True)

    class Meta:
        model = Episode
        fields = ("id", "title", "secondary_title", "short_title", "episode_number", "telecast_date",
                  "language", "channel", "content_type", "content_subject", "content_synopsis", "characters",
                  "set_in_location", "created_on", "modified_on", "episodesegment_set", "episodetranslationjob_set")


class DetailSeriesSerializer(serializers.ModelSerializer):
    episode_set = SimpleEpisodeSerializer(many=True, read_only=True, )
    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )

    number_of_episodes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Series
        fields = ("id", "title", "alternate_title", "short_title", "version", "part", "rating", "year_of_release",
                  "number_of_episodes", "genre", "episode_set", "poster",  "cast", "cbfc", "status", "remark")

    def get_number_of_episodes(self, obj):
        return Episode.objects.filter(series=obj).count()


class CreateMovieSerializer(serializers.ModelSerializer):
    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )

    class Meta:
        model = Movie
        fields = "__all__"
        read_only_fields = ("id",)


class CreateMovieSegmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = MovieSegment
        fields = '__all__'
        read_only_fields = ("id",)


class MovieSegmentSerializer(serializers.ModelSerializer):
    video = VideoSerializer(many=False, read_only=True)

    class Meta:
        model = MovieSegment
        fields = '__all__'
        read_only_fields = ("id",)


class PromoSegmentSerializer(serializers.ModelSerializer):
    video = VideoSerializer(many=False, read_only=True)

    class Meta:
        model = PromoSegment
        fields = '__all__'
        read_only_fields = ("id",)


class DetailMovieTranslationJobSerializer(serializers.ModelSerializer):
    movie_segment = MovieSegmentSerializer()
    created_by = UserSerializer(many=False, read_only=True)
    assigned_to = UserSerializer(many=False, read_only=True)

    class Meta:
        model = MovieTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'movie_segment', 'created_by', 'assigned_to', "source_subtitle", "target_subtitle", "target_language")
        read_only_fields = ("id", 'created_on', "modified_on")


class NxMovieSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    trivia_count = serializers.SerializerMethodField(read_only=True)
    trivia_stat = serializers.SerializerMethodField(read_only=True)
    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )

    class Meta:
        model = Movie
        fields = ("id", "poster", "movie_title", 'secondary_title', "short_title", "year_of_release", "language", "genre",
                  "content_subject", "content_synopsis", "characters", "created_on", "modified_on",  "channel",
                  "trivia_count", "trivia_stat")
        read_only_fields = ("id",)

    def get_trivia_count(self, obj):
        return Trivia.objects.filter(movie=obj).count()

    def get_trivia_stat(self, obj):
        res = {}
        res['approved'] = Trivia.objects.filter(
            Q(movie=obj) & Q(is_approved="yes")).count()
        res['disapproved'] = Trivia.objects.filter(
            Q(movie=obj) & Q(is_approved="no")).count()
        res['new'] = Trivia.objects.filter(
            Q(movie=obj) & Q(is_approved="false")).count()
        res['rewritten'] = Trivia.objects.filter(movie=obj).exclude(
            trivia=F("original_description")).count()
        res['rewritten_new'] = Trivia.objects.filter(Q(movie=obj) & Q(
            is_approved="false")).exclude(trivia=F("original_description")).count()
        return res


class CreatePersonSerializer(serializers.ModelSerializer):
    actor = ActorSerializer(many=False, allow_null=True)
    politician = CreatePoliticianWithoutPersonSerializer(
        many=False, allow_null=True)

    class Meta:
        model = Person
        fields = ("id", "name", "dob", "born_location", "picture", "current_location", "description", "father_name", "mother_name",
                  "partner_name", "religion", "caste", "occupation", "education", "charatcer_played", "actor", "politician")
        read_only_fields = ("id",)
        extra_kwargs = {'actor': {'required': False}, 'politician': {'required': False},
                        'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}

    def create(self, validated_data):
        actor_data = validated_data.pop('actor')
        politician_data = validated_data.pop('politician')
        person = Person.objects.create(**validated_data)
        if any(x in person.occupation for x in ["actor", "Actor", "actress", "Actress"]) and actor_data:
            Actor.objects.create(person=person, **actor_data)
        if any(x in person.occupation for x in ["politician", "Politician"]) and politician_data:
            Politician.objects.create(person=person, **politician_data)
        return person

    def update(self, instance, validated_data):
        print(validated_data)
        logger.debug(validated_data)
        actor_data = validated_data.pop('actor')
        politician_data = validated_data.pop('politician')
        logger.debug(actor_data)
        instance.name = validated_data.get('name', instance.name)
        instance.dob = validated_data.get('dob', instance.dob)
        instance.born_location = validated_data.get(
            'born_location', instance.born_location)
        instance.current_location = validated_data.get(
            "current_location", instance.current_location)
        instance.description = validated_data.get(
            "description", instance.description)
        instance.father_name = validated_data.get(
            "father_name", instance.father_name)
        instance.mother_name = validated_data.get(
            "mother_name", instance.mother_name)
        instance.partner_name = validated_data.get(
            "partner_name", instance.partner_name)
        instance.religion = validated_data.get("religion", instance.religion)
        instance.caste = validated_data.get("caste", instance.caste)
        instance.occupation = validated_data.get(
            "occupation", instance.occupation)
        instance.education = validated_data.get(
            "education", instance.education)
        instance.save()

        if (actor_data is not None) and any(x in instance.occupation for x in ["actor", "Actor", "actress", "Actress"]):
            actor, created = Actor.objects.get_or_create(person=instance)
            actor.active_from = actor_data.get(
                "active_from", actor.active_from)
            actor.active_till = actor_data.get(
                "active_till", actor.active_till)
            actor.awards = actor_data.get("awards", actor.awards)
            actor.save()
        if (politician_data is not None) and any(x in instance.occupation for x in ["politician", "Politician"]):
            politician, created = Politician.objects.get_or_create(
                person=instance)
            politician.description = politician_data.get(
                "description", politician.description)
            politician.political_party = politician_data.get(
                "political_party", politician.political_party)
            politician.constituency = politician_data.get(
                "constituency", politician.constituency)
            politician.positions = politician_data.get(
                "positions", politician.positions)
            politician.save()

        return instance


class TagSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=TagCategory.objects.all(), slug_field='name')

    class Meta:
        model = Tag
        fields = ('id', 'name', 'category', 'created_on', 'modified_on')


class SoftMovieSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "movie_title", 'secondary_title', "short_title", "year_of_release", "language", "genre",
                  "content_subject", "content_synopsis", "characters", "created_on", "modified_on",  "channel")
        read_only_fields = ("id",)


class TriviaSerializer(serializers.ModelSerializer):
    persons = PersonSerializer(many=True, read_only=True)
    movie = SoftMovieSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Trivia
        fields = ("id", "url", "persons", "trivia", "movie", "tags", "created_by", "created_on", "modified_on",
                  "source", "is_approved", "approved_by", "disapproved_reason", "original_description", "edit_request",
                  "edit_status")


class DetailTriviaSerializer(serializers.ModelSerializer):
    persons = PersonSerializer(many=True, read_only=True)
    movie = SoftMovieSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    play_count = serializers.SerializerMethodField()
    song_count = serializers.SerializerMethodField()

    class Meta:
        model = Trivia
        fields = ("id", "persons", "trivia", "movie", "tags", "created_by", "created_on", "modified_on",
                  "source", "is_approved", "approved_by", "disapproved_reason", "original_description",
                  "play_count", "song_count", "edit_request", "edit_status")

    def get_play_count(self, obj):
        t = TriviaLog.objects.filter(trivia=obj).count()
        return t

    def get_song_count(self, obj):
        t = TriviaLog.objects.filter(trivia=obj).values(
            'playlist_entry__object_id').distinct().count()
        return t


class TriviaChannelSerializer(serializers.ModelSerializer):
    poster = VersatileImageFieldSerializer(
        sizes='video_poster'
    )
    latest_trivia = serializers.SerializerMethodField()
    stat = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = ("id", "channel_name", "parent_company",
                  "poster", "latest_trivia", "stat")

    def get_latest_trivia(self, obj):
        t = TriviaLog.objects.filter(playlist_entry__playlist__channel=obj)
        if t:
            latest_trivia_log = t.latest('timestamp')
            ser = DetailTriviaSerializer(latest_trivia_log.trivia)
            return ser.data
        else:
            return None

    def get_stat(self, obj):
        t = TriviaLog.objects.filter(playlist_entry__playlist__channel=obj)
        if not t:
            return {"today": 0, "last_week": 0, "last_month": 0}
        else:
            time_before_24hrs = datetime.now() - timedelta(hours=24)
            time_before_168hrs = datetime.now() - timedelta(hours=168)
            time_before_30days = datetime.now() - timedelta(hours=720)
            today = t.filter(Q(modified_on__gte=time_before_24hrs)).count()
            last_week = t.filter(
                Q(modified_on__gte=time_before_168hrs)).count()
            last_month = t.filter(
                Q(modified_on__gte=time_before_30days)).count()
            return {"today": today, "last_month": last_month, "last_week": last_week}


class CreateTriviaSerializer(serializers.ModelSerializer):
    movie = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False, queryset=Movie.objects.all(), allow_null=True)
    persons = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=Person.objects.all(),
                                                 allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False, queryset=Tag.objects.all())

    class Meta:
        model = Trivia
        fields = ("movie", "persons", "trivia", 'tags', 'created_by', "disapproved_reason", "source", "is_approved",
                  "edit_request",
                  "edit_status")
        extra_kwargs = {'created_by': {
            'default': serializers.CurrentUserDefault()}}

    def update(self, instance, validated_data):
        raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        # Log trivia edit request changes
        initial_value = None
        if not instance.edit_request:
            initial_value = instance.trivia
        else:
            initial_value = instance.edit_request
        if validated_data.get('edit_request') and (validated_data.get('edit_request') != initial_value):
            trivia_edit_log = TriviaEditLog.objects.create(trivia=instance, edited_on=datetime.now(),
                                                           trivia_before=initial_value,
                                                           trivia_after=validated_data.get(
                                                               'edit_request'),
                                                           user=self.context['request'].user)
            trivia_edit_log.save()

        # log review status change
        if (instance.edit_status != validated_data.get('edit_status')) or (instance.is_approved != validated_data.get('is_approved')):
            trivia_review_log = TriviaReviewLog.objects.create(trivia=instance, timestamp=datetime.now(),
                                                               is_approved_before=instance.is_approved,
                                                               is_approved_after=validated_data.get(
                                                                   'is_approved'),
                                                               edit_status_before=instance.edit_status,
                                                               edit_status_after=validated_data.get(
                                                                   'edit_status'),
                                                               user=self.context['request'].user)
            trivia_review_log.save()

        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                field = getattr(instance, attr)
                field.set(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance


class LoadTriviaSerializer(serializers.Serializer):
    actor_name = serializers.CharField()
    occupation = serializers.CharField()
    trivia = serializers.ListField(
        child=serializers.CharField(max_length=1024))
    original_description = serializers.ListField(
        child=serializers.CharField(max_length=1024))


class LoadMovieTriviaSerializer(serializers.Serializer):
    name = serializers.CharField()
    year = serializers.IntegerField()
    trivia = serializers.ListField(
        child=serializers.CharField(max_length=1024))
    original_description = serializers.ListField(
        child=serializers.CharField(max_length=1024))


class LoadGenericTriviaSerializer(serializers.Serializer):
    actors = serializers.ListField(
        child=serializers.CharField(max_length=1024))
    singers = serializers.ListField(
        child=serializers.CharField(max_length=1024))
    movie = serializers.CharField(allow_null=True)
    director = serializers.CharField(allow_null=True)
    is_approved = serializers.CharField(
        max_length=3, default='CLN', allow_blank=True)
    trivia = serializers.ListField(
        child=serializers.CharField(max_length=1024))
    original_description = serializers.ListField(
        child=serializers.CharField(max_length=1024))


class UpdateTriviaSerializer(serializers.Serializer):
    actor_name = serializers.CharField()
    trivia = serializers.ListField(
        child=serializers.CharField(max_length=1024))
    original = serializers.ListField(
        child=serializers.CharField(max_length=2014))


class PersonGroupSerializer(serializers.ModelSerializer):
    persons = DetailPersonSerializer(many=True, read_only=True)

    class Meta:
        model = PersonGroup
        fields = "__all__"


class CreatePersonGroupSerializer(serializers.ModelSerializer):
    persons = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False, queryset=Person.objects.all())

    class Meta:
        model = PersonGroup
        fields = ("title", "persons")


class PlaylistSerializer(serializers.ModelSerializer):

    class Meta:
        model = Playlist
        fields = "__all__"


class PlaylistEntryRelatedField(serializers.RelatedField):

    def to_representation(self, value):
        if isinstance(value, Song):
            serializer = SongSerializer(value)
        if isinstance(value, NxSong):
            serializer = NxSongSerializer(value)
        elif isinstance(value, Movie):
            serializer = MovieSerializer(value)
        else:
            raise Exception('Unexpected type of tagged object')

        return serializer.data


class PlaylistEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = PlaylistEntry
        fields = "__all__"


class CreateTriviaLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = TriviaLog
        fields = '__all__'


class TriviaLogSerializer(serializers.ModelSerializer):
    trivia = DetailTriviaSerializer()
    playlist_entry = serializers.SlugField()
    media_id = serializers.SerializerMethodField()

    class Meta:
        model = TriviaLog
        fields = ("id", "trivia", "timestamp", "created_on",
                  "modified_on", "playlist_entry", "media_id")

    def get_media_id(self, obj):
        c = ContentType.objects.get(app_label='content', model='nxsong')
        if obj.playlist_entry.content_type == c:
            return obj.playlist_entry.content_object.content_id
        else:
            return None


class DetailPlaylistSerializer(serializers.ModelSerializer):
    channel = TriviaChannelSerializer()
    entries = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ("id", "channel", "date", "active", "created_on", "modified_on",
                  "entries")

    def get_entries(self, obj):
        qs = PlaylistEntry.objects.filter(playlist=obj)
        data = []
        for value in qs:
            s_data = None
            trivia_logs = TriviaLog.objects.filter(playlist_entry=value)
            if isinstance(value.content_object, Song):
                serializer = SongSerializer(value.content_object)
                s_data = serializer.data
                s_data['start_time'] = value.start_time
                s_data['end_time'] = value.end_time
                s_data['trivia_logs'] = TriviaLogSerializer(
                    trivia_logs, many=True).data
            elif isinstance(value.content_object, Movie):
                serializer = MovieSerializer(value.content_object)
                s_data = serializer.data
                s_data['start_time'] = value.start_time
                s_data['end_time'] = value.end_time
                s_data['trivia_logs'] = TriviaLogSerializer(
                    trivia_logs, many=True).data
            else:
                raise Exception('Unexpected type of tagged object')
            data.append(s_data)
        return data


class SongSerializer(serializers.ModelSerializer):

    class Meta:
        model = Song
        fields = ("id", "title", "year", "released_on", "label",
                  "movie", "genre", "producers", "song_writers", "singers", "music_directors",
                  "actors", "language", "movie_directors", "duration", "tempo",
                  "lyrics", "version", "original_remake")


class NxSongSerializer(serializers.ModelSerializer):
    music_directors = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(), many=True, allow_empty=True, allow_null=False)
    producers = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(), many=True, allow_empty=True, allow_null=False)
    actors = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(), many=True, allow_empty=True, allow_null=False)
    singers = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(), many=True, allow_empty=True, allow_null=False)
    song_writers = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(), many=True, allow_empty=True, allow_null=False)

    class Meta:
        model = NxSong
        fields = ("id", "created_on", "modified_on", "title", "label", "released_on",
                  "recorded_on", "recorded_in", "movie", "genre", "producers", "song_writers", "singers",
                  "length", "music_directors", "actors", "is_processed", "video", "content_id")


class LabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Label
        fields = "__all__"


class TriviaEditLogSerializer(serializers.ModelSerializer):
    trivia = TriviaSerializer(read_only=True)

    class Meta:
        model = TriviaEditLog
        fields = ("user", "trivia", "trivia_before",
                  "trivia_after", "edited_on")


class TriviaReviewLogSerializer(serializers.ModelSerializer):
    trivia = TriviaSerializer(read_only=True)

    class Meta:
        model = TriviaReviewLog
        fields = ("user", "trivia", "is_approved_before", "is_approved_after",
                          "edit_status_before", "edit_status_after", "timestamp")


class ChannelClipSerializer(serializers.ModelSerializer):
    video = VideoSerializer(read_only=True)
    stat = serializers.SerializerMethodField(read_only=True)
    channel_code = serializers.SerializerMethodField(read_only=True)
    total_song_count = serializers.SerializerMethodField(read_only=True)
    marked_song_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChannelClip
        fields = ("url", "id", "video", "start_time", "end_time", "date", "channel", "channel_code", "created_on",
                  "modified_on", "stat", "filled_duration", "total_song_count", "marked_song_count")

    def get_channel_code(self, obj):
        return obj.channel.channel_code

    def get_stat(self, obj):
        btags = PlayoutTag.objects.filter(video=obj.video)
        res = {}
        res['accepted'] = btags.filter(Q(is_approved='ACP')).count()
        res['not accepted'] = btags.filter(Q(is_approved='NCP')).count()
        res['new'] = btags.filter(
            Q(is_approved='CLN') | Q(is_approved=None)).count()
        res['total'] = btags.count()
        return res

    def get_total_song_count(self, obj):
        btags = PlayoutTag.objects.filter(video=obj.video)
        return btags.count()

    def get_marked_song_count(self, obj):
        btags = PlayoutTag.objects.filter(
            video=obj.video, object_id__isnull=False)
        return btags.count()


class CreateChannelClipSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChannelClip
        fields = ("id", "video", "start_time", "end_time",
                  "date", "channel", "created_on", "modified_on")


class BarcChannelSerializer(serializers.ModelSerializer):
    poster = VersatileImageFieldSerializer(
        sizes='video_poster'
    )
    duration = serializers.SerializerMethodField(read_only=True)
    stat = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Channel
        fields = ("id", "channel_name", "channel_code",
                  "parent_company", "poster", "duration", "stat")

    def get_duration(self, obj):
        channelclips = ChannelClip.objects.filter(channel=obj)
        dur = 0
        for c in channelclips:
            if c.video:
                dur += c.video.duration
        return str(timedelta(seconds=int(dur)))

    def get_stat(self, obj):
        res = {}
        res['accepted'] = 0
        res['not accepted'] = 0
        res['new'] = 0
        res['total'] = 0
        return res


class SongVerificationSerializer(serializers.ModelSerializer):
    """Serializer for Song QC"""
    class Meta:
        model = SongVerification
        fields = "__all__"


class AssetVersionSerializer(serializers.ModelSerializer):
    """Serializer for Asset Version"""

    class Meta:
        model = AssetVersion
        fields = '__all__'
        extra_kwargs = {'created_by': {
            'default': serializers.CurrentUserDefault(), "read_only": True}}


class WorkFlowStepSerializer(serializers.ModelSerializer):
    workgroup = WorkGroupSerializer(many=False, read_only=True)

    class Meta:
        model = WorkFlowStep
        fields = "__all__"


class WorkFlowStageSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkFlowStage
        fields = "__all__"


class DetailedWorkFlowStageSerializer(serializers.ModelSerializer):
    prev_step = WorkFlowStepSerializer(many=False, read_only=True)
    next_step = WorkFlowStepSerializer(many=False, read_only=True)

    class Meta:
        model = WorkFlowStage
        fields = "__all__"


class WorkFlowSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkFlow
        fields = "__all__"

    def assign_permissions(self, user, wf):
        permission_list = [
            "org_view_workflow", "team_view_workflow", "user_view_workflow",
            "org_change_workflow", "team_change_workflow", "user_change_workflow",
            "org_delete_workflow", "team_delete_workflow", "user_delete_workflow",
        ]
        for permission in permission_list:
            for group in Group.objects.filter(user=user, permissions__codename=permission):
                assign_perm(permission, group, wf)

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        project = WorkFlow.objects.create(**validated_data)
        self.assign_permissions(user, wf)
        return wf

class DetailedWorkFlowSerializer(serializers.ModelSerializer):
    work_flow_stage = DetailedWorkFlowStageSerializer(
        many=True, read_only=True)

    class Meta:
        model = WorkFlow
        fields = "__all__"


class WorkFlowInstanceMembershipSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkFlowInstanceMembership
        fields = "__all__"


class WorkFlowInstanceSerializer(serializers.ModelSerializer):
    asset_version = serializers.PrimaryKeyRelatedField(
        many=True, queryset=AssetVersion.objects.all())

    class Meta:
        model = WorkFlowInstance
        fields = "__all__"

    def assign_permissions(self, user, wfi):
        permission_list = [
            "org_view_workflowinstance", "team_view_workflowinstance", "user_view_workflowinstance",
            "org_change_workflowinstance", "team_change_workflowinstance", "user_change_workflowinstance",
            "org_delete_workflowinstance", "team_delete_workflowinstance", "user_delete_workflowinstance",
        ]
        for permission in permission_list:
            for group in Group.objects.filter(user=user, permissions__codename=permission):
                assign_perm(permission, group, wfi)

    def create(self, validated_data):
        """
        We have a bit of extra checking around this in order to provide
        descriptive messages when something goes wrong, but this method is
        essentially just:
                return ExampleModel.objects.create(**validated_data)
        If there are many to many fields present on the instance then they
        cannot be set until the model is instantiated, in which case the
        implementation is like so:
                example_relationship = validated_data.pop('example_relationship')
                instance = ExampleModel.objects.create(**validated_data)
                instance.example_relationship = example_relationship
                return instance
        The default implementation also does not handle nested relationships.
        If you want to support writable nested relationships you'll need
        to write an explicit `.create()` method.
        """
        raise_errors_on_nested_writes('create', self, validated_data)

        ModelClass = self.Meta.model

        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)

        try:
            request = self.context.get("request")
            user = request.user
            instance = ModelClass._default_manager.create(**validated_data)
            self.assign_permissions(user,instance)
        except TypeError:
            tb = traceback.format_exc()
            msg = (
                'Got a `TypeError` when calling `%s.%s.create()`. '
                'This may be because you have a writable field on the '
                'serializer class that is not a valid argument to '
                '`%s.%s.create()`. You may need to make the field '
                'read-only, or override the %s.create() method to handle '
                'this correctly.\nOriginal exception was:\n %s' %
                (
                    ModelClass.__name__,
                    ModelClass._default_manager.name,
                    ModelClass.__name__,
                    ModelClass._default_manager.name,
                    self.__class__.__name__,
                    tb
                )
            )
            raise TypeError(msg)

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                if field_name == "asset_version":
                    for asset_version_instance in value:
                        workflow_instance_membership_instance = WorkFlowInstanceMembership.objects.create(
                            asset_version=asset_version_instance, work_flow_instance=instance)
                else:
                    field = getattr(instance, field_name)
                    field.set(value)
        return instance

    def update(self, instance, validated_data):
        raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)

        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.
        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)

        instance.save()

        # Note that many-to-many fields are set after updating instance.
        # Setting m2m fields triggers signals which could potentially change
        # updated instance and we do not want it to collide with .update()
        for attr, value in m2m_fields:
            if attr == "asset_version":
                for asset_version_instance in value:
                    if not WorkFlowInstanceMembership.objects.filter(asset_version__id=asset_version_instance.id):
                        workflow_instance_membership_instance = WorkFlowInstanceMembership.objects.create(
                            asset_version=asset_version_instance, work_flow_instance=instance)
                WorkFlowInstanceMembership.objects.filter(
                    work_flow_instance=instance).exclude(asset_version__in=value).delete()
            else:
                field = getattr(instance, attr)
                field.set(value)

        return instance


class AssignWorkFlowInstanceStepSerializer(serializers.ModelSerializer):
    """ Serializer for assigning the workflowinstancestep"""
    class Meta:
        model = AssignWorkFlowInstanceStep
        fields = "__all__"


class DetailedAssignWorkFlowInstanceStepSerializer(serializers.ModelSerializer):
    """ Serializer for assigning the workflowinstancestep"""
    assigned_to = UserSerializer(many=False, read_only=True)
    assigned_by = UserSerializer(many=False, read_only=True)

    class Meta:
        model = AssignWorkFlowInstanceStep
        fields = "__all__"


class WorkFlowInstanceStepSerializer(serializers.ModelSerializer):
    work_flow_step = WorkFlowStepSerializer(many=False, read_only=True)
    # reverse FK with related_name
    assigned = DetailedAssignWorkFlowInstanceStepSerializer(
        many=True, read_only=True)

    class Meta:
        model = WorkFlowInstanceStep
        fields = "__all__"
        ordering = ['created_on']

    def assign_permissions(self, user, wfis):
        permission_list = [
            "org_view_workflowinstancestep", "team_view_workflowinstancestep", "user_view_workflowinstancestep",
            "org_change_workflowinstancestep", "team_change_workflowinstancestep", "user_change_workflowinstancestep",
            "org_delete_workflowinstancestep", "team_delete_workflowinstancestep", "user_delete_workflowinstancestep",
        ]
        for permission in permission_list:
            for group in Group.objects.filter(user=user, permissions__codename=permission):
                assign_perm(permission, group, wfis)

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        wfis = WorkFlowInstanceStep.objects.create(**validated_data)
        self.assign_permissions(user, wfis)
        return project

class DetailedWorkFlowInstanceSerializer(serializers.ModelSerializer):
    work_flow = WorkFlowSerializer(many=False, read_only=True)
    # reverse FK with related_name
    # work_flow_instance_steps = WorkFlowInstanceStepSerializer(many=True, read_only=True)

    asset_version = WorkFlowInstanceMembershipSerializer(
        source="workflow_to_asset", many=True, read_only=True)

    work_flow_instance_steps = serializers.SerializerMethodField(
        read_only=True)  # to accomodate ordering by created_on

    class Meta:
        model = WorkFlowInstance
        fields = ('id', 'work_flow', 'asset_version',
                  'work_flow_instance_steps', 'due_date')

    def get_work_flow_instance_steps(self, obj):
        return WorkFlowInstanceStepSerializer(WorkFlowInstanceStep.objects.filter(work_flow_instance__id=obj.id).order_by('created_on'), many=True, context=self.context).data


class WorkFlowCollectionInstanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkFlowCollectionInstance
        fields = "__all__"


class AssignWorkFlowCollectionInstanceStepSerializer(serializers.ModelSerializer):
    """ Serializer for assigning the workflowcollectioninstancestep"""
    class Meta:
        model = AssignWorkFlowCollectionInstanceStep
        fields = "__all__"


class DetailedAssignWorkFlowCollectionInstanceStepSerializer(serializers.ModelSerializer):
    """ Serializer for assigning the workflowcollectioninstancestep"""
    assigned_to = UserSerializer(many=False, read_only=True)
    assigned_by = UserSerializer(many=False, read_only=True)

    class Meta:
        model = AssignWorkFlowCollectionInstanceStep
        fields = "__all__"


class WorkFlowCollectionInstanceStepSerializer(serializers.ModelSerializer):
    work_flow_step = WorkFlowStepSerializer(many=False, read_only=True)
    # reverse FK with related_name
    assigned = DetailedAssignWorkFlowCollectionInstanceStepSerializer(
        many=True, read_only=True)

    class Meta:
        model = WorkFlowCollectionInstanceStep
        fields = "__all__"
        ordering = ['created_on']


class DetailedWorkFlowCollectionInstanceSerializer(serializers.ModelSerializer):
    work_flow = WorkFlowSerializer(many=False, read_only=True)

    work_flow_instance_steps = serializers.SerializerMethodField(
        read_only=True)  # to accomodate ordering by created_on

    class Meta:
        model = WorkFlowCollectionInstance
        fields = ('id', 'work_flow', 'collection',
                  'work_flow_instance_steps', 'due_date')

    def get_work_flow_instance_steps(self, obj):
        return WorkFlowCollectionInstanceStepSerializer(WorkFlowCollectionInstanceStep.objects.filter(work_flow_instance__id=obj.id).order_by('created_on'), many=True, context=self.context).data


class WorkFlowTransitionHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkFlowTransitionHistory
        fields = "__all__"


class DetailedAssetVersionSerializer(serializers.ModelSerializer):
    """Serializer for Asset Version"""
    video = VideoSerializer(many=False, read_only=True)
    created_by = UserSerializer(many=False, read_only=True)
    language = ContentLanguageSerializer(many=False, read_only=True)
    audio_languages = ContentLanguageSerializer(many=True, read_only=True)
    subtitle_languages = ContentLanguageSerializer(many=True, read_only=True)

    # reverse FK with related_name
    work_flow_instances = DetailedWorkFlowInstanceSerializer(
        many=True, read_only=True)

    class Meta:
        model = AssetVersion
        fields = '__all__'


class DetailedSearchAssetVersionSerializer(serializers.ModelSerializer):
    """Serializer for Asset Version"""
    video = VideoSerializer(many=False, read_only=True)
    created_by = UserSerializer(many=False, read_only=True)
    work_flow_details = serializers.SerializerMethodField(read_only=True)
    search_times = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AssetVersion
        fields = '__all__'

    def get_work_flow_details(self, obj):
        work_flow_instance = WorkFlowInstance.objects.filter(
            asset_version=obj).first()
        if work_flow_instance:
            return DetailedWorkFlowInstanceSerializer(work_flow_instance, many=False, context=self.context).data

    def get_search_times(self, obj):
        return obj.search_times


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for the Create New Collection"""
    class Meta:
        model = Collection
        fields = '__all__'
        # read_only_fields = ("id")


class DetailedCollectionSerializer(serializers.ModelSerializer):
    """Serializer for the Create New Collection"""
    created_by = UserSerializer(many=False, read_only=True)
    asset_version = DetailedAssetVersionSerializer(many=True, read_only=True)
    segments = serializers.SerializerMethodField(read_only=True)

    # reverse FK with related_name
    work_flow_instances = DetailedWorkFlowCollectionInstanceSerializer(
        many=True, read_only=True)

    class Meta:
        model = Collection
        fields = '__all__'

    def get_segments(self, obj):
        frame_tag_count = FrameTag.objects.filter(
            collection=obj, tag__title="Segment").count()
        return frame_tag_count


class SegmentSerializer(serializers.ModelSerializer):
    """Serializer for a segment"""
    class Meta:
        model = Segment
        fields = "__all__"


class PromoSerializer(serializers.ModelSerializer):
    """Serializer for a promo"""
    class Meta:
        model = Promo
        fields = "__all__"


class PromoTitleSerializer(serializers.ModelSerializer):
    """Serializer for a promo"""
    channel = ChannelSerializer(read_only=True)
    genre = GenreSerializer(read_only=False, many=True)
    language = ContentLanguageSerializer(many=False, read_only=True)

    class Meta:
        model = Promo
        fields = ('title', 'secondary_title', 'short_title', 'aka_title', 'promo_number', 'language', 'channel', 'genre', 'year_of_release', 'synopsis',
                  'certification', 'notes', 'country_of_origin',)


class PromoCastSerializer(serializers.ModelSerializer):
    """Serializer for a promo"""
    directors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    actors = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)

    class Meta:
        model = Promo
        fields = ('actors', 'directors', 'producers', 'dop', 'screenplay',)


class DetailedPromoSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    # asset_version = DetailedAssetVersionSerializer(read_only=True, many=True)
    asset_version = serializers.SerializerMethodField(
        read_only=True)  # to accomodate ordering by created_on
    directors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    actors = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    genre = GenreSerializer(read_only=False, many=True)
    language = ContentLanguageSerializer(read_only=False, many=False)

    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )

    class Meta:
        model = Promo
        fields = "__all__"
        read_only_fields = ("id",)

    def get_asset_version(self, obj):
        return DetailedAssetVersionSerializer(AssetVersion.objects.filter(object_id=obj.id).order_by('-created_on'), many=True, context=self.context).data


class CognitiveSearchPromoSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    directors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    actors = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    genre = GenreSerializer(read_only=False, many=True)
    language = ContentLanguageSerializer(read_only=False, many=False)

    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )

    class Meta:
        model = Promo
        fields = ("id", "title", "short_title", "language", "year_of_release", "channel", "producers", "actors", "directors", "ingested_on",
                  "dop", "screenplay", "location", "cbfc", "status", "remark", "genre", "promo_number", "synopsis", "aka_title", "certification",
                  "timecode_in", "notes", "country_of_origin", "unpackaged_master", "sequence", "created_on", "modified_on", "modified_by", "created_by", "poster")
        read_only_fields = ("id",)


class RushesSerializer(serializers.ModelSerializer):
    """Serializer for Rushes"""
    class Meta:
        model = Rushes
        fields = "__all__"


class DetailedRushesSerializer(serializers.ModelSerializer):
    """Serializer for Rushes"""
    channel = ChannelSerializer(read_only=True)
    # moviesegment_set = MovieSegmentSerializer(many=True, read_only=True)
    # movietranslationjob_set = DetailMovieTranslationJobSerializer(many=True, read_only=True)
    # trivia_count = serializers.SerializerMethodField(read_only=True)
    # asset_version = DetailedAssetVersionSerializer(read_only=True, many=True)
    asset_version = serializers.SerializerMethodField(read_only=True)
    # cast = PersonSerializer(many=True)
    directors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    actors = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    genre = GenreSerializer(read_only=False, many=True)
    language = ContentLanguageSerializer(read_only=False, many=False)
    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )

    class Meta:
        model = Rushes
        fields = "__all__"
        read_only_fields = ("id",)

    def get_asset_version(self, obj):
        return DetailedAssetVersionSerializer(AssetVersion.objects.filter(object_id=obj.id).order_by('-created_on'), many=True, context=self.context).data


class CognitiveSearchRushesSerializer(serializers.ModelSerializer):
    """Serializer for Rushes"""
    channel = ChannelSerializer(read_only=True)
    directors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    actors = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    genre = GenreSerializer(read_only=False, many=True)
    language = ContentLanguageSerializer(read_only=False, many=False)

    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )

    class Meta:
        model = Rushes
        fields = ("id", "title", "year_of_release", "language", "channel", "genre", "content_subject", "synopsis", "producers", "ingested_on",
                  "actors", "directors", "dop", "screenplay", "mood", "event_name", "event_location", "created_on", "modified_on", "modified_by", "created_by", "poster")
        read_only_fields = ("id",)


class MovieSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    language = ContentLanguageSerializer(read_only=False, many=False)
    asset_version = serializers.SerializerMethodField(read_only=True)
    genre = GenreSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    directors = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    # makers = PersonSerializer(read_only=False, many=True)
    actors = PersonSerializer(read_only=False, many=True)
    created_by = UserSerializer(many=False, read_only=True)
    production_house = ProductionHouseSerializer(read_only=False)
    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )

    class Meta:
        model = Movie
        fields = ("id", "poster", "title", "short_title", "year_of_release", "language", "genre",
                  "content_subject", "created_on", "modified_on",  "channel", "cbfc", "status", "remark", "asset_version",
                  "location", "cbfc", "remark", "aka_title", "production_house", "keywords",
                  "status", "certification", "classification", "slot_duration",
                  "tx_run_time", "external_ref_number", "barcode", "tx_id", "synopsis", "short_synopsis",
                  "actors", "rank", "part_description", "country_of_origin", "created_by", "screenplay", "dop", "directors", "producers")
        read_only_fields = ("id",)

    def get_asset_version(self, obj):
        return DetailedAssetVersionSerializer(AssetVersion.objects.filter(object_id=obj.id), many=True, context=self.context).data


class DetailSongSerializer(serializers.ModelSerializer):
    label = LabelSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)
    producers = PersonSerializer(read_only=True, many=True)
    actors = PersonSerializer(read_only=True, many=True)
    music_directors = PersonSerializer(read_only=True, many=True)
    singers = PersonSerializer(read_only=True, many=True)
    song_writers = PersonSerializer(read_only=True, many=True)

    verified = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Song
        fields = ("id", "title", "year", "released_on", "recorded_on", "recorded_in", "label",
                  "movie", "genre", "producers", "song_writers", "singers", "length", "music_directors",
                  "actors", "language", "verified", "movie_directors", "duration", "tempo", "lyrics",
                  "version", "original_remake")

    def get_verified(self, obj):
        verified = SongVerification.objects.filter(song=obj)
        if not verified:
            return False
        return True


class ContentTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContentType
        fields = "__all__"


class MetadataAudioSerializer(serializers.ModelSerializer):

    class Meta:
        model = MetadataAudio
        fields = "__all__"


class SongAssetSerializer(serializers.ModelSerializer):

    class Meta:
        model = SongAsset
        fields = "__all__"


class DetailedSongAssetSerializer(serializers.ModelSerializer):
    # asset_version = DetailedAssetVersionSerializer(read_only=True, many=True)
    asset_version = serializers.SerializerMethodField(read_only=True)
    directors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    actors = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    singers = PersonSerializer(read_only=False, many=True)
    genre = GenreSerializer(read_only=False, many=True)
    channel = ChannelSerializer(read_only=True)
    language = ContentLanguageSerializer(read_only=False, many=False)
    song_writers = PersonSerializer(read_only=False, many=True)
    label = LabelSerializer(read_only=False)

    class Meta:
        model = SongAsset
        fields = "__all__"

    def get_asset_version(self, obj):
        return DetailedAssetVersionSerializer(AssetVersion.objects.filter(object_id=obj.id).order_by('-created_on'), many=True, context=self.context).data


class CognitiveSearchSongAssetSerializer(serializers.ModelSerializer):
    directors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    actors = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    singers = PersonSerializer(read_only=False, many=True)
    genre = GenreSerializer(read_only=False, many=True)
    channel = ChannelSerializer(read_only=True)
    language = ContentLanguageSerializer(read_only=False, many=False)
    song_writers = PersonSerializer(read_only=False, many=True)
    label = LabelSerializer(read_only=False)

    class Meta:
        model = SongAsset
        fields = ("id", "title", "channel", "label", "year", "released_on", "recorded_on",
                  "genre", "language", "producers", "actors", "directors", "dop", "screenplay", "song_writers", "singers", "location", "tempo", "lyrics",
                  "version", "original_remake", "synopsis", "movie", "aka_title", "album", "production_house", "keywords", "status", "certification",
                  "classification", "slot_duration", "tx_run_time", "external_ref_number", "barcode", "tx_id", "rank", "part_description", "country_of_origin",
                  "created_by", "modified_by", "created_on", "modified_on", "ingested_on",)


class BatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Batch
        fields = "__all__"


class VideoProcessingStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = VideoProcessingStatus
        fields = "__all__"


class SequenceSerializer(serializers.ModelSerializer):

    segments = serializers.SerializerMethodField(read_only=True)

    def get_segments(self, obj):
        return SegmentSerializer(Segment.objects.filter(sequence=obj), many=True, context=self.context).data

    class Meta:
        model = Sequence
        fields = "__all__"


class EpisodeSerializer(serializers.ModelSerializer):
    # asset_version = DetailedAssetVersionSerializer(read_only=True, many=True)
    asset_version = serializers.SerializerMethodField(read_only=True)
    actors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    directors = PersonSerializer(read_only=False, many=True)

    def get_asset_version(self, obj):
        return DetailedAssetVersionSerializer(AssetVersion.objects.filter(object_id=obj.id).order_by('-created_on'), many=True, context=self.context).data

    class Meta:
        model = Episode
        fields = "__all__"


class CognitiveSearchEpisodeSerializer(serializers.ModelSerializer):
    actors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    directors = PersonSerializer(read_only=False, many=True)

    class Meta:
        model = Episode
        fields = ("id", "title", "secondary_title", "short_title", "episode_number", "telecast_date",
                  "language", "content_type", "content_subject", "synopsis", "characters",
                  "set_in_location", "producers", "actors", "dop", "screenplay", "directors",
                  "created_on", "modified_on", "series_no", "tx_order", "keywords", "status",
                  "external_ref_number", "certification", "classification", "slot_duration",
                  "tx_run_time", "part", "barcode", "tx_id", "short_synopsis", "rank", "role")


class SeasonSerializer(serializers.ModelSerializer):
    episodes = EpisodeSerializer(many=True, read_only=True)
    actors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    directors = PersonSerializer(read_only=False, many=True)

    class Meta:
        model = Season
        fields = ("id", "title", "secondary_title", "short_title", "episodes", "telecast_date",
                  "language", "content_type", "content_subject", "synopsis", "characters",
                  "set_in_location", "producers", "actors", "dop", "screenplay", "directors",
                  "created_on", "modified_on")
        # episodes explicitly added in fields and is a related name for reverse
        # FK relation in Episode model


class CognitiveSearchSeasonSerializer(serializers.ModelSerializer):
    actors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    directors = PersonSerializer(read_only=False, many=True)

    class Meta:
        model = Season
        fields = ("id", "title", "secondary_title", "short_title", "telecast_date",
                  "language", "content_type", "content_subject", "synopsis", "characters",
                  "set_in_location", "producers", "actors", "dop", "screenplay", "directors",
                  "created_on", "modified_on")


class DetailedSeriesSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    seasons = SeasonSerializer(many=True, read_only=True)
    genre = GenreSerializer(read_only=False, many=True)
    actors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    language = ContentLanguageSerializer(read_only=False, many=False)
    production_house = ProductionHouseSerializer(read_only=False)
    directors = PersonSerializer(read_only=False, many=True)

    class Meta:
        model = Series
        fields = ("id", "title", "alternate_title", "short_title", "seasons", "version", "part", "rating", "year_of_release",
                  "number_of_episodes", "genre", "poster", "cbfc", "status", "remark", "channel", "producers",
                  "actors", "dop", "directors", "screenplay", "language", "series_no", "programme_id",
                  "production_number", "production_house", "compilation", "certification", "classification",
                  "sequence", "slot_duration", "tx_run_time", "content_subject", "external_ref_number",
                  "barcode", "tx_id", "synopsis", "short_synopsis", "rank")
        # seasons explicitly added in fields and is a related name for reverse
        # FK relation in Season model


class CreateSeriesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Series
        fields = "__all__"


class CognitiveSearchSeriesSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    genre = GenreSerializer(read_only=False, many=True)
    actors = PersonSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    language = ContentLanguageSerializer(read_only=False, many=False)
    production_house = ProductionHouseSerializer(read_only=False)

    class Meta:
        model = Series
        fields = ("id", "title", "alternate_title", "short_title", "version", "part", "rating", "year_of_release",
                  "number_of_episodes", "genre", "poster", "cbfc", "status", "remark", "channel", "producers",
                  "actors", "dop", "directors", "screenplay", "language", "series_no", "programme_id",
                  "production_number", "production_house", "compilation", "certification", "classification",
                  "sequence", "slot_duration", "tx_run_time", "content_subject", "external_ref_number",
                  "barcode", "tx_id", "synopsis", "short_synopsis", "rank")


class CreateSeasonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Season
        fields = "__all__"


class CommercialAssetSerializer(serializers.ModelSerializer):
    # language = ContentLanguageSerializer(read_only = False, many =False)

    class Meta:
        model = CommercialAsset
        fields = "__all__"


class DetailedCommercialAssetSerializer(serializers.ModelSerializer):
    language = ContentLanguageSerializer(read_only=False, many=False)
    asset_version = serializers.SerializerMethodField(read_only=True)
    channel = ChannelSerializer(read_only=True)
    production_house = ProductionHouseSerializer(read_only=False)

    class Meta:
        model = CommercialAsset
        fields = "__all__"

    def get_asset_version(self, obj):
        return DetailedAssetVersionSerializer(AssetVersion.objects.filter(object_id=obj.id).order_by('-created_on'), many=True, context=self.context).data


class CognitiveSearchCommercialAssetSerializer(serializers.ModelSerializer):
    language = ContentLanguageSerializer(read_only=False, many=False)
    # asset_version = serializers.SerializerMethodField(read_only= True)
    channel = ChannelSerializer(read_only=True)
    production_house = ProductionHouseSerializer(read_only=False)

    class Meta:
        model = CommercialAsset
        fields = ("id", "title", "aka_title", "production_house", "product_code", "language", "ingested_on",
                  "year_of_release", "synopsis", "remark", "channel", "created_on", "modified_on", "created_by", "country_of_origin")


class CognitiveSearchMovieSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    language = ContentLanguageSerializer(read_only=False, many=False)
    # asset_version = serializers.SerializerMethodField(read_only= True)
    genre = GenreSerializer(read_only=False, many=True)
    producers = PersonSerializer(read_only=False, many=True)
    directors = PersonSerializer(read_only=False, many=True)
    dop = PersonSerializer(read_only=False, many=True)
    screenplay = PersonSerializer(read_only=False, many=True)
    # makers = PersonSerializer(read_only=False, many=True)
    actors = PersonSerializer(read_only=False, many=True)
    created_by = UserSerializer(many=False, read_only=True)
    production_house = ProductionHouseSerializer(read_only=False)

    class Meta:
        model = Movie
        fields = ("id", "title", "short_title", "year_of_release", "language", "channel", "genre",
                  "content_subject", "producers", "directors", "dop", "screenplay", "location", "created_on", "modified_on",
                  "ingested_on", "cbfc", "remark", "aka_title", "production_house", "keywords", "status", "certification",
                        "classification", "slot_duration", "tx_run_time", "external_ref_number", "barcode",
                        "tx_id", "synopsis", "short_synopsis", "actors", "rank", "part_description", "country_of_origin", "created_by")


class DemoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Demo
        fields = "__all__"

class NewCategoriesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Folder
        fields = ["title"]

class CategoriesSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ("id", "title", "count")

    def get_count(self, obj):
        checker = ObjectPermissionChecker(self.context['request'].user)
        fol = [f for f in Folder.objects.filter(category=obj.id) if checker.has_perm('user_view_folder', f) or checker.has_perm('org_view_folder', f) or checker.has_perm('team_view_folder', f)]
        fil = [f for f in File.objects.filter(category=obj.id) if checker.has_perm('user_view_file', f) or checker.has_perm('org_view_file', f) or checker.has_perm('team_view_file', f)]
        return len(fil) + len(fol)

class ChannelsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Channel
        fields = ("id", "channel_name")

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Folder
        fields= ("id", "title")

class ContentsSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Folder
        fields = "__all__"

class FilesSerializer(serializers.ModelSerializer):

    class Meta:
        model = File
        fields = "__all__"

class FolderSerializer(serializers.ModelSerializer):
    contents = serializers.SerializerMethodField()
    channel = ChannelsSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    parent_folders = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ("id", "created_on", "channel", "contents", "title", "parent", "category", "title_metadata", 'parent_folders')


    def get_contents(self, obj):
        folders = Folder.objects.filter(parent=obj.id)
        files = File.objects.filter(location=obj.id)
        contents = list(chain(set(files) | set(folders)))
        results = []
        for content in contents:
            content_type = content.__class__.__name__.lower()
            if isinstance(content, Folder):
                ser = ContentsSerializer(content)
            if isinstance(content, File):
                ser = FileSerializer(content)
            results.append({"type": content_type, "data": ser.data})
        return results

    def get_parent_folders(self, obj):
        if obj.parent is None:
            return []
        folder_list = self.get_parent_folders(obj.parent)
        parent = obj.parent
        folder_list.append({parent.title: parent.id})
        return folder_list

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        folder = Folder.objects.create(validated_data)
        assign_perm('view_folder', user, folder)
        assign_perm('change_folder', user, folder)
        assign_perm('delete_folder', user, folder)
        return folder

class FolderSearchSerializer(serializers.ModelSerializer):

    class Meta:
        model = ("id", "title", "created_on")

class NewFolderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Folder
        fields = ("id", "created_on", "channel", "title", "parent", "category", "title_metadata",)
        extra_kwargs = {
            'created_by': {
                'default': serializers.CurrentUserDefault(), 
                "read_only": True
            },
            'modified_by': {
                'default': serializers.CurrentUserDefault(), 
            }
        }

    def assign_folder_permissions(self, user, folder):
        permission_list = [
            "org_view_folder", "team_view_folder", "user_view_folder",
            "org_change_folder", "team_change_folder", "user_change_folder",
            "org_delete_folder", "team_delete_folder", "user_delete_folder",
        ]
        for permission in permission_list:
            for group in Group.objects.filter(user=user, permissions__codename=permission):
                assign_perm(permission, group, folder)

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        folder = Folder.objects.create(**validated_data)
        self.assign_folder_permissions(user, folder)
        return folder

class NewFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = File
        fields = "__all__"
        extra_kwargs = {
            'created_by': {
                'default': serializers.CurrentUserDefault(), 
                "read_only": True
            },
            'modified_by': {
                'default': serializers.CurrentUserDefault(), 
            }
        }

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        file = File.objects.create(**validated_data)
        groups = Group.objects.filter(user=request.user,permissions__codename__contains="file").distinct()
        for group in groups:
            for permission in group.permissions.values_list("codename", flat=True):
                assign_perm(permission, group, file)
        return file

class FileSerializer(serializers.ModelSerializer):

    class Meta:
        model = File
        fields = "__all__"

class RelatedCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ("id","user","comment", "submit_datetime", "replies")

    def get_replies(self, obj):
        return RelatedCommentSerializer(Comment.objects.filter(object_id=obj.id), many=True).data

class WorkFlowMetadataSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkFlowMetadata
        fields = ("id", "workflow", "field_name", "field_type", "placeholder", "opt_values")
        extra_kwargs = {
            'created_by': {
                'default': serializers.CurrentUserDefault(), 
                "read_only": True
            },
            'modified_by': {
                'default': serializers.CurrentUserDefault(), 
            }
        }

class ProjectMetadataSerializer(serializers.ModelSerializer):
    workflow_metadata = WorkFlowMetadataSerializer(read_only=True)

    class Meta:
        model = ProjectMetadata
        fields = "__all__"

class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Projects
        fields = ('id', 'name', 'description', 'workflow')
        extra_kwargs = {
            'created_by': {
                'default': serializers.CurrentUserDefault(), 
                "read_only": True
            },
            'modified_by': {
                'default': serializers.CurrentUserDefault(), 
            }
        }

    def assign_permissions(self, user, project):
        permission_list = [
            "org_view_projects", "team_view_projects", "user_view_projects",
            "org_change_projects", "team_change_projects", "user_change_projects",
            "org_delete_projects", "team_delete_projects", "user_delete_projects",
        ]
        for permission in permission_list:
            for group in Group.objects.filter(user=user, permissions__codename=permission):
                assign_perm(permission, group, project)

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        project = Projects.objects.create(**validated_data)
        self.assign_permissions(user, project)
        return project

class ProjectVersionSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    workflow_instance = DetailedWorkFlowInstanceSerializer(read_only=True)
    user_comments = RelatedCommentSerializer(read_only=True, many=True)

    class Meta:
        model = ProjectVersion
        fields = "__all__"
        extra_kwargs = {
            'created_by': {
                'default': serializers.CurrentUserDefault(), 
                "read_only": True
            },
            'modified_by': {
                'default': serializers.CurrentUserDefault(), 
            }
        }

    def assign_permissions(self, user, projectv):
        permission_list = [
            "org_view_projectversion", "team_view_projectversion", "user_view_projectversion",
            "org_change_projectversion", "team_change_projectversion", "user_change_projectversion",
            "org_delete_projectversion", "team_delete_projectversion", "user_delete_projectversion",
        ]
        for permission in permission_list:
            for group in Group.objects.filter(user=user, permissions__codename=permission):
                assign_perm(permission, group, projectv)

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        projectv = ProjectVersion.objects.create(**validated_data)
        self.assign_permissions(user, projectv)
        return projectv


class CreateProjectVersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectVersion
        fields = "__all__"
        extra_kwargs = {
            'created_by': {
                'default': serializers.CurrentUserDefault(), 
                "read_only": True
            },
            'modified_by': {
                'default': serializers.CurrentUserDefault(), 
            }
        }

class DetailedProjectSerializer(serializers.ModelSerializer):
    workflow = WorkFlowSerializer(read_only=True)
    project_version = serializers.SerializerMethodField()
    project_metadata = serializers.SerializerMethodField()

    class Meta:
        model = Projects
        fields = ("id", "name", "workflow", "description", "created_on", "created_by", "project_version", "project_metadata")
        extra_kwargs = {
            'created_by': {
                'default': serializers.CurrentUserDefault(), 
                "read_only": True
            },
            'modified_by': {
                'default': serializers.CurrentUserDefault(), 
            }
        }

    def get_project_version(self, obj):
        return ProjectVersionSerializer(ProjectVersion.objects.filter(project__id=obj.id).order_by("-created_on").first()).data

    def get_project_metadata(self, obj):
        return DetailedProjectMetadataSerializer(ProjectMetadata.objects.filter(project=obj), many=True).data

class ProjectFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectFiles
        fields = "__all__"
        extra_kwargs = {
            'created_by': {
                'default': serializers.CurrentUserDefault(), 
                "read_only": True
            },
            'modified_by': {
                'default': serializers.CurrentUserDefault(), 
            }
        }

class DetailedProjectFileSerializer(serializers.ModelSerializer):
    file = FileSerializer(read_only=True)

    class Meta:
        model = ProjectFiles
        fields = "__all__"
        extra_kwargs = {
            'created_by': {
                'default': serializers.CurrentUserDefault(), 
                "read_only": True
            },
            'modified_by': {
                'default': serializers.CurrentUserDefault(), 
            }
        }


class ProjectMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMetadata
        fields = ("id", "workflow_metadata", "project", "value")
        extra_kwargs = {
            'created_by': {
                'default': serializers.CurrentUserDefault(), 
                "read_only": True
            },
            'modified_by': {
                'default': serializers.CurrentUserDefault(), 
            }
        }
        
class DetailedProjectMetadataSerializer(serializers.ModelSerializer):
    workflow_metadata = WorkFlowMetadataSerializer(read_only=True)

    class Meta:
        model = ProjectMetadata
        fields = ("id", "workflow_metadata", "project", "value")
        extra_kwargs = {
            'created_by': {
                'default': serializers.CurrentUserDefault(), 
                "read_only": True
            },
            'modified_by': {
                'default': serializers.CurrentUserDefault(), 
            }
        }
