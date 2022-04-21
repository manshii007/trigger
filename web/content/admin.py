#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.contrib import admin
from django.http import HttpResponseRedirect
from .models import ProjectFiles, ProjectMetadata, ProjectVersion, Projects, Trivia, NxSong, Song, Movie, Person, Channel, MovieSegment, Series, Episode, PersonGroup, CloudPerson, Politician, EpisodeSegment, WorkFlowInstance, \
                     WorkFlow, WorkFlowMetadata, WorkFlowStep, WorkFlowStage, WorkFlowTransitionHistory, File, Folder
from contextual.models import Face, FaceGroup
import nested_admin
from admin import admin_site
from guardian.admin import GuardedModelAdmin
from tools.core.tools import CF
from .tasks import upload_to_azure_cloud
from custom.filters import MovieTitleFilter, TriviaFilter, ActorFilter, PersonFilter, MovieFilter, SeriesFilter, LanguageFilter, ChannelFilter


class SongAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('title', 'language')
    filter_horizontal = ('actors', 'music_directors', 'producers', 'singers', 'song_writers')
    list_filter = (ActorFilter, LanguageFilter)


admin.site.register(Song, SongAdmin)


class NxSongAdmin(admin.ModelAdmin):
    search_fields = ('title', 'content_id')
    list_display = ('title', 'content_id')
    filter_horizontal = ('actors', 'music_directors', 'producers', 'singers', 'song_writers')
    list_filter = (ActorFilter,)


admin.site.register(NxSong, NxSongAdmin)


class TriviaAdmin(admin.ModelAdmin):
    search_fields = ("trivia", "persons__name", "movie__movie_title")
    fields = ('trivia', 'edit_request', 'persons', 'movie', 'edit_status', 'disapproved_reason', 'tags')
    list_display = ("trivia", "edit_status")
    filter_horizontal = ("persons", 'movie', 'tags')
    list_filter = ('edit_status', TriviaFilter, PersonFilter, MovieTitleFilter)


admin.site.register(Trivia, TriviaAdmin)


class EpisodeAdmin(GuardedModelAdmin):
    search_fields = ("title", "secondary_title", "short_title", "season__title")
    list_display = ("title", "season")
    list_filter = ("telecast_date", LanguageFilter) #SeriesFilter
    filter_horizontal = ("characters",)


admin.site.register(Episode, EpisodeAdmin)

admin.site.register(EpisodeSegment)


class SeriesAdmin(GuardedModelAdmin):
    search_fields = ("title", "short_title", "alternate_title")
    list_display = ("title", "rating", "year_of_release", "number_of_episodes")
    filter_horizontal = ("genre",)


admin.site.register(Series, SeriesAdmin)


class MovieAdmin(GuardedModelAdmin):
    search_fields = ("title", "secondary_title", "short_title")
    list_display = ("title", "channel")
    list_filter = (ChannelFilter, MovieFilter)
    filter_horizontal = ["genre"]


admin.site.register(Movie, MovieAdmin)
admin.site.register(MovieSegment)


class ChannelAdmin(GuardedModelAdmin):
    pass


admin.site.register(Channel, ChannelAdmin)


class FaceInline(nested_admin.NestedTabularInline):
    model = Face
    fields = ('face_img', )
    readonly_fields = ('face_img',)
    extra = 0


class FaceGroupInline(nested_admin.NestedTabularInline):
    model = FaceGroup
    fields = (('id', 'person'),)
    readonly_fields = ('id', 'person')
    inlines = [
        FaceInline,
    ]
    extra = 0


class PersonInline(nested_admin.NestedTabularInline):
    model = Person
    inlines = [
        FaceGroupInline
    ]


@admin.register(Person)
class PersonAdmin(nested_admin.NestedModelAdmin):
    list_display = ('name', 'id')
    inlines = [
        FaceGroupInline,
    ]


def start_training(modeladmin, request, queryset):
    for personGroup in queryset:
        personGroup.start_training()

start_training.description = "Start Cloud Training"


def upload_to_cloud(modeladmin, request, queryset):
    upload_to_azure_cloud.delay([ele.id for ele in queryset])
    if len(queryset) == 1:
        url = '/admin/content/persongroup/{}/change'.format(queryset[0].id)
        return HttpResponseRedirect(url)
upload_to_cloud.description = "Upload Models to Cloud"


@admin.register(PersonGroup)
class PersonGroupAdmin(nested_admin.NestedModelAdmin):
    fields = ('id', 'title', 'persons', 'upload_progress', 'get_training_status')
    readonly_fields = ('id', 'get_training_status', 'upload_progress')
    actions = [
        start_training,
        upload_to_cloud
    ]


class CloudPersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'person', 'cloud_id')


@admin.register(Politician)
class PoliticianAdmin(admin.ModelAdmin):
    list_display = ('person',)


admin_site.register(Person, PersonAdmin)
admin_site.register(PersonGroup)
admin.site.register(CloudPerson, CloudPersonAdmin)
admin.site.register(WorkFlow)
admin.site.register(WorkFlowStep)
admin.site.register(WorkFlowInstance)
admin.site.register(WorkFlowStage)
admin.site.register(WorkFlowTransitionHistory)
admin.site.register(File)
admin.site.register(Folder)
admin.site.register(Projects)
admin.site.register(ProjectFiles)
admin.site.register(ProjectVersion)
admin.site.register(WorkFlowMetadata)
admin.site.register(ProjectMetadata)