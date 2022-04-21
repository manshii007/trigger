#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from rest_framework import serializers

from .models import (
    User,
    Profile
)
from jobs.models import EpisodeTranslationJob, MovieTranslationJob
from content.serializers import (
    MovieSegmentSerializer,
    EpisodeSegmentSerializer,
    ChannelSerializer,
    SeriesSerializer,
)
from content.models import Episode, Movie
from workgroups.serializers import DetailMembershipSerializer
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    membership = DetailMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'is_superuser','membership', 'first_name', 'last_name')

class CreateUserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'auth_token', 'email', 'first_name', 'last_name')
        read_only_fields = ('auth_token',)
        extra_kwargs = {'password': {'write_only': True}}


class DetailProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ('user',)


class DetailUserSerializer(serializers.ModelSerializer):
    profile = DetailProfileSerializer(many=False, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'profile', 'first_name', 'last_name')


class CheckUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False, read_only=True)
    class Meta:
        model = Profile
        fields = ('id', 'url', 'user')


class EpisodeSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    series = SeriesSerializer(read_only=True)

    class Meta:
        model = Episode
        fields = ("id", "episode_title", "secondary_title", "short_title", "series", "episode_number", "telecast_date",
                  "language", "channel", "content_type", "genre", "content_subject", "content_synopsis", "characters",
                  "set_in_location", "created_on", "modified_on")


class DetailEpisodeTranslationJobSerializer(serializers.ModelSerializer):
    episode = EpisodeSerializer()
    episode_segment = EpisodeSegmentSerializer()

    class Meta:
        model = MovieTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'episode', 'episode_segment', 'created_by', 'assigned_to', "source_subtitle", "target_subtitle",
                  "target_language")
        read_only_fields = ("id", 'created_on', "modified_on")


class MovieSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = Movie
        fields = ("id", "movie_title", 'secondary_title', "short_title", "year_of_release", "language", "genre",
                  "content_subject", "content_synopsis", "characters", "created_on", "modified_on",  "channel")
        read_only_fields = ("id",)


class DetailMovieTranslationJobSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()
    movie_segment = MovieSegmentSerializer()

    class Meta:
        model = MovieTranslationJob
        fields = ("id", "created_on", "modified_on", "due_date", 'job_status', 'priority',
                  'movie', 'movie_segment', 'created_by', 'assigned_to', "source_subtitle", "target_subtitle", "target_language")
        read_only_fields = ("id", 'created_on', "modified_on")


class DetailJobUserSerializer(serializers.ModelSerializer):
    profile = DetailProfileSerializer(many=False, read_only=True)
    episode_translation_job_assigned = DetailEpisodeTranslationJobSerializer(many=True, read_only=True)
    movie_translation_job_assigned = DetailMovieTranslationJobSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'profile', "episode_translation_job_assigned",
                  "movie_translation_job_assigned")


class NotificationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    recipient = UserSerializer(User, read_only=True)
    unread = serializers.BooleanField(read_only=True)
    verb = serializers.CharField()
    actor = UserSerializer(User, read_only=True)
    timestamp = serializers.DateTimeField()

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

class ProfilePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint through profile
    """
    id = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    old_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value
