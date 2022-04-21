from django_filters.rest_framework import FilterSet
import django_filters

from .models import (
    Person,
    Character,
    Channel,
    Genre,
    Episode,
    Projects,
    Series,
    ContextType,
    Politician,
    TVAnchor,
    Movie,
    EpisodeSegment,
    MovieSegment,
    Trivia,
    Playlist,
    Promo,
    TriviaEditLog,
    Season,
    Rushes,
)


class TriviaEditLogFilter(FilterSet):
    class Meta:
        model = TriviaEditLog
        fields = ("user", "trivia")


class PersonFilter(FilterSet):
    dob_filter = django_filters.DateFromToRangeFilter(name="dob")
    trivia__isnull = django_filters.rest_framework.BooleanFilter(name="trivia", lookup_expr='isnull', distinct=True)

    class Meta:
        model = Person
        fields = {
            "name": ['exact', 'contains', 'icontains', 'istartswith'],
            "dob_filter": ['exact'],
            "born_location": ['exact', 'contains', 'icontains'],
            "description": ['exact', 'contains', 'icontains'],
            "occupation": ['exact', 'contains', 'icontains'],
            'trivia__isnull': ['exact'],
        }


class TriviaFilter(FilterSet):
    movie = django_filters.CharFilter(name="movie__movie_title", lookup_expr='icontains')
    actor = django_filters.CharFilter(name="persons__name", lookup_expr='icontains')
    occupation = django_filters.CharFilter(name="persons__occupation", lookup_expr='icontains')
    tags = django_filters.CharFilter(name="tags__name", lookup_expr='icontains')

    class Meta:
        model = Trivia
        fields = ("movie", "actor", "tags", 'occupation', "is_approved", "edit_status")


class CharacterFilter(FilterSet):
    original_name = django_filters.CharFilter(name="actor__name")
    series = django_filters.CharFilter(name="series__title")

    class Meta:
        model = Character
        fields = ("character_name", "original_name", "series")


# class SeriesFilter(FilterSet):
#     channel_name = django_filters.CharFilter(name="channel__channel_name")
#     compliance_status = django_filters.CharFilter(name="episode__episodesegment__video__compliancestatustag__is_approved")

#     class Meta:
#         model = Series
#         fields = {"title": ['exact', 'contains', 'icontains', 'istartswith'],
#                   "channel_name": ['exact', 'contains', 'icontains', 'istartswith'],
#                   "compliance_status": ['exact', 'contains', 'icontains', 'istartswith']
#                   }

class SeasonFilter(FilterSet):
    series = django_filters.UUIDFilter(name="series__id")
    title = django_filters.CharFilter(name="title")
    class Meta:
        model = Season
        fields = {
                    "title": ['exact'],
                    "series": ['exact'],
                }

class GenreFilter(FilterSet):
    class Meta:
        model = Genre
        fields = ("title",)


class ChannelFilter(FilterSet):
    class Meta:
        model = Channel
        fields = ("channel_name",)


class ContextTypeFilter(FilterSet):
    class Meta:
        model = ContextType
        fields = ("type_name",)


class EpisodeFilter(FilterSet):
    season = django_filters.CharFilter(name="season__title")
    characters = django_filters.CharFilter(name="characters__character_name")
    actors = django_filters.CharFilter(name="characters__actor__name")

    class Meta:
        model = Episode
        fields = ("title", "season", "characters", "actors")


class PoliticianFilter(FilterSet):
    name = django_filters.CharFilter(name="person__name")

    class Meta:
        model = Politician
        fields = ("political_party", "positions", "name", "constituency")


class TVAnchorFilter(FilterSet):
    name = django_filters.CharFilter(name="person__name")

    class Meta:
        model = TVAnchor
        fields = ("organizations", "notable_credits", "awards", "name", "books")


class MovieFilter(FilterSet):
    characters = django_filters.CharFilter(name="characters__character_name")
    actors = django_filters.CharFilter(name="characters__actor__name")
    channel_name = django_filters.CharFilter(name="channel__channel_name")
    compliance_status = django_filters.CharFilter(name="moviesegment__video__compliancestatustag__is_approved")

    class Meta:
        model = Movie
        fields = {"title": ['exact', 'contains', 'icontains', 'istartswith'],
                  "characters": ['exact', 'contains', 'icontains', 'istartswith'],
                  "channel_name": ['exact', 'contains', 'icontains', 'istartswith'],
                  "actors": ['exact', 'contains', 'icontains', 'istartswith'],
                  "compliance_status": ['exact', 'contains', 'icontains', 'istartswith']
                  }

class CaseInsensitiveBooleanFilter(django_filters.Filter):

    def filter(self, qs, value):
        if value is not None:
            lc_value = value.lower()
            if lc_value == "true":
                value = True
            elif lc_value == "false":
                value = False
            return qs.filter(**{self.name: value})
        return qs

class PromoFilter(FilterSet):
    # compliance_status = django_filters.CharFilter(name="moviesegment__video__compliancestatustag__is_approved")
    assigned_to = django_filters.UUIDFilter(name="asset_version__work_flow_instances__work_flow_instance_steps__assigned__assigned_to")
    channel = django_filters.CharFilter(name="channel")
    is_tagged = CaseInsensitiveBooleanFilter(name="asset_version__is_tagged")

    class Meta:
        model = Promo
        fields = {"assigned_to", "channel", "is_tagged"}

class RushesFilter(FilterSet):
    assigned_to = django_filters.UUIDFilter(name="asset_version__work_flow_instances__work_flow_instance_steps__assigned__assigned_to")
    channel = django_filters.CharFilter(name="channel")
    is_tagged = CaseInsensitiveBooleanFilter(name="asset_version__is_tagged")

    class Meta:
        model = Rushes
        fields = {"assigned_to", "channel", "is_tagged"}

class SeriesFilter(FilterSet):
    assigned_to = django_filters.UUIDFilter(name="seasons__episodes__asset_version__work_flow_instances__work_flow_instance_steps__assigned__assigned_to")
    channel = django_filters.UUIDFilter(name="channel__id")
    title = django_filters.CharFilter(name="title")
    is_tagged = CaseInsensitiveBooleanFilter(name="asset_version__is_tagged")

    class Meta:
        model = Series
        fields = {"assigned_to":['exact', 'contains', 'icontains', 'istartswith'],
                "channel": ['exact'],
                "is_tagged" : ['exact', 'contains', 'icontains', 'istartswith'],
                "title" : ['exact'],}

class NodeStatusFilter(django_filters.Filter):

    def filter(self, qs, value):

        if value not in (None, ''):
            values = value.split('|')
            for each_value in values:
                title, status = each_value.split(":")
                qs = qs.filter(**{'projectversion__workflow_instance__work_flow_instance_steps__work_flow_step__title': title, 'projectversion__workflow_instance__work_flow_instance_steps__work_flow_step_status': status})
        return qs

class ProjectMetadataFilter(django_filters.Filter):

    def filter(self, qs, value):

        if value not in (None, ''):
            values = value.split('|')
            for each_value in values:
                metadata, metadata_value = each_value.split(":")
                qs = qs.filter(**{'projectversion__project__projectmetadata__workflow_metadata__field_name': metadata, 'projectversion__project__projectmetadata__value': metadata_value})
        return qs

class ProjectFilter(FilterSet):
    work_flow_node_status = NodeStatusFilter(name="projectversion__workflow_instance__work_flow_instance_steps")
    project_metadata = ProjectMetadataFilter(name="projectversion__project__projectmetadata__workflow_metadata")

    class Meta:
        model = Projects
        fields = {"work_flow_node_status", "project_metadata"}