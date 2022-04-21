from django.contrib import admin
from .models import Face, FaceGroup, HardCuts, PictureGroup, VideoFaceGroup
import nested_admin
from frames.models import PictureFrame


@admin.register(Face)
class FaceAdmin(admin.ModelAdmin):
    list_display = ('face_img', 'id', 'azure_face_id', 'face_group')


class FaceInline(admin.TabularInline):
    model = Face
    fields = ('face_img', 'azure_face_id', 'face_img_url')
    readonly_fields = ('face_img', 'face_img_url', 'azure_face_id')


@admin.register(FaceGroup)
class FaceGroupAdmin(admin.ModelAdmin):
    inlines = [
        FaceInline,
    ]
    list_display = ('profile_img', 'id', 'person')
    fields = ('person',)

admin.site.register(HardCuts)

admin.site.register(VideoFaceGroup)


class FrameInline(nested_admin.NestedTabularInline):
    model = PictureFrame
    fields = ('full_img', 'id')
    list_display = ('full_img',)


class RelationInline(nested_admin.NestedTabularInline):
    model = PictureGroup.frames.through
    inline = [
        FrameInline
    ]


@admin.register(PictureGroup)
class PictureGroupAdmin(nested_admin.NestedModelAdmin):
    readonly_fields = ('name',)

