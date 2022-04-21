from django.contrib import admin
from .tasks import backgroud_face_detection, background_face_grouping, backgroud_face_recon
from .models import Frames, Rect, VideoFrame, PictureFrame, ProxyFrame
import nested_admin
from contextual.models import Face

# admin.site.register(Frames)
admin.site.register(VideoFrame)
admin.site.register(Rect)
# admin.site.register(PictureFrame)
# admin.site.register(ProxyFrame)


class FaceInline(nested_admin.NestedTabularInline):
    model = Face
    fields = ('face_img', 'person_name')
    readonly_fields = ('face_img', 'person_name')
    show_change_link = True
    extra = 0


class RectInline(nested_admin.NestedTabularInline):
    model = Rect
    inlines = [
        FaceInline,
    ]
    show_change_link = True
    exclude = ('x','y','w','h','tags')
    extra = 0


def process_for_face_detection(modeladmin, request, queryset):
    for frame in queryset:
        backgroud_face_detection.delay(frame.id)
process_for_face_detection.description = "Process Frame for Face Detection"


def process_for_face_grouping(modeladmin, request, queryset):
    background_face_grouping.delay()
process_for_face_grouping.description = "Process Frame for Face Grouping"


def process_for_face_recon(modeladmin, request, queryset):
    for frame in queryset:
        backgroud_face_recon.delay(frame.id)
process_for_face_recon.description = "Process Frame for Face Recon"


@admin.register(Frames)
class FrameAdmin(nested_admin.NestedModelAdmin):
    model = Frames
    inlines = [
        RectInline,
    ]
    list_display = ('full_img',)
    fields = ('full_img',)
    readonly_fields = ('full_img',)
    actions = [
        process_for_face_detection,
        process_for_face_grouping,
        process_for_face_recon
    ]
    search_fields = ['rects__face__face_group__person__name']


@admin.register(PictureFrame)
class PictureFrameAdmin(nested_admin.NestedModelAdmin):
    model = PictureFrame
    list_display = ('full_img',)
    fields = ('full_img',)
    readonly_fields = ('full_img',)


@admin.register(ProxyFrame)
class ProxyFrameAdmin(nested_admin.NestedModelAdmin):
    model = ProxyFrame
    list_display = ('full_img',)
    fields = ('full_img', 'id', 'file')
    readonly_fields = ('full_img', 'id')
