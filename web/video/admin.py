#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.contrib import admin
from admin import admin_site
from django.http import HttpResponseRedirect
from jobs.models import JobType, AutoVideoJob
from .models import (
    VideoLibrary,
    Video
)


import nested_admin
from contextual.models import FaceGroup, Face
from content.forms import SeriesForm, MovieForm
from content.models import EpisodeSegment, Episode, Series
from django.contrib import messages
from django.shortcuts import render
from guardian.admin import GuardedModelAdmin



admin.site.register(VideoLibrary)


def process_for_face_detection(modeladmin, request, queryset):
    for video in queryset:
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Faces')
        auto = AutoVideoJob.objects.create(created_by=request.user, video=video,
                                           job_type=job_type_instance, eta=0.0)
        if len(queryset) == 1:
            url = '/admin/jobs/autovideojob/{}/change'.format(auto.id)
            return HttpResponseRedirect(url)

process_for_face_detection.description = "Process Video for Face Detection"


def process_for_face_matching(modeladmin, request, queryset):
    for video in queryset:
        job_type_instance, _ = JobType.objects.get_or_create(name='Match Faces')
        auto = AutoVideoJob.objects.create(created_by=request.user, video=video,
                                           job_type=job_type_instance, eta=0.0)
        if len(queryset) == 1:
            url = '/admin/jobs/autovideojob/{}/change'.format(auto.id)
            return HttpResponseRedirect(url)
process_for_face_matching.description = "Process Video for Face Matching"


def process_for_objects(modeladmin, request, queryset):
    for video in queryset:
        job_type_instance, _ = JobType.objects.get_or_create(name='Identify Objects')
        auto = AutoVideoJob.objects.create(created_by=request.user, video=video,
                                           job_type=job_type_instance, eta=1800)
process_for_objects.descripition = "Process Video for labels"


class FaceInline(nested_admin.NestedTabularInline):
    model = Face
    fields = ('face_img', 'azure_face_id')
    readonly_fields = ('face_img',)


class FaceGroupInline(nested_admin.NestedTabularInline):
    model = FaceGroup
    # list_display = (, 'person')
    fields = ('profile_img', 'person',)
    readonly_fields = ('profile_img', 'person',)
    extra = 1
    # inlines = [
    #     FaceInline,
    # ]


@admin.register(Video)
class VideoAdmin(GuardedModelAdmin, nested_admin.NestedModelAdmin):
    list_display = ('title', 'poster_img')
    fields = ('id', ('poster_img','title'), 'poster', ('created_on', 'duration'), ('height', 'width'), ('total_frames',
              'frame_rate'), 'file', 'is_removed', 'video_player')
    readonly_fields = ('id', 'created_on', 'duration', 'height', 'width', 'total_frames',
                       'frame_rate', 'poster_img', 'video_player')



    inlines = [
        FaceGroupInline,
    ]

    def create_episodes(self, request, queryset):
        if 'do_action' in request.POST:
            form = SeriesForm(request.POST)
            if form.is_valid():
                series = form.cleaned_data['series']
                series_obj = series
                episodes = []
                for v in queryset:
                    episode_num = v.title.split("_")[-1]
                    episode = Episode.objects.create(episode_title=v.title, series=series_obj,
                                                     channel=series_obj.channel, episode_number=int(episode_num)
                                                     )
                    es = EpisodeSegment.objects.create(episode=episode, video=v)
                    episodes.append(episode)
                messages.success(request, '{0} episodes were created'.format(len(episodes)))
                return
        else:
            form = SeriesForm()

        return render(request, 'admin/create_episodes.html',
                      {'title': u'Choose Series',
                       'objects': queryset,
                       'form': form})

    create_episodes.short_description = u'Create episodes of selected videos'

    actions = [
        process_for_face_detection,
        process_for_face_matching,
        create_episodes,
        process_for_objects]



admin_site.register(Video, VideoAdmin)