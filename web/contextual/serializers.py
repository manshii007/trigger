from rest_framework import serializers
from .models import HardCuts, FaceGroup, Face
from content.serializers import PersonSerializer, CharacterSerializer


class FaceGroupSerializer(serializers.ModelSerializer):
    face_image = serializers.URLField(source='face_img', read_only=True)
    poster = serializers.URLField(source='face_img', read_only=True)
    modified_timeline = serializers.SerializerMethodField(read_only=True)
    timeline = serializers.SerializerMethodField(read_only=True)
    person = PersonSerializer()
    character = CharacterSerializer()
    timeline_length = serializers.SerializerMethodField(read_only=True)
    duration = serializers.SerializerMethodField(read_only=True)
    name = serializers.SerializerMethodField(read_only=True)
    type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FaceGroup
        fields = ('id', 'url', 'face_image', 'person', 'character', 'modified_timeline', 'timeline',
                 'poster', 'timeline_length', 'duration', "name", "type", 'created_on', 'modified_on')
        read_only_fields = ("face_image", "poster")

    def get_type(self, obj):
        return 'facegroup'

    def get_name(self, obj):
        if obj.person:
            return obj.person.name
        else:
            return ""

    def get_modified_timeline(self, obj):
        modified_timeline = []
        for i in range(int(len(obj.timeline)/2)):
            modified_timeline.append({"startTime":obj.timeline[i*2], "endTime":obj.timeline[i*2+1]})
        return modified_timeline

    def get_timeline(self, obj):
        modified_timeline = []
        for i in range(int(len(obj.timeline)/2)):
            modified_timeline.append({"startTime":obj.timeline[i*2], "endTime":obj.timeline[i*2+1]})
        return modified_timeline

    def get_timeline_length(self, obj):
        return len(obj.timeline)

    def get_duration(self, obj):
        duration = 0
        for i in range(int(len(obj.timeline) / 2)):
            duration += obj.timeline[i*2+1] - obj.timeline[i*2]
        return duration

class UpdateFaceGroupSerializer(serializers.ModelSerializer):
    face_image = serializers.URLField(source='face_img', read_only=True)
    timeline = serializers.SerializerMethodField(read_only=True)
    # person = PersonSerializer()

    class Meta:
        model = FaceGroup
        fields = ('id', 'url', 'person', 'character', 'timeline', 'face_image')
        read_only_fields = ("face_image",)

    def get_timeline(self, obj):
        modified_timeline = []
        for i in range(int(len(obj.timeline)/2)):
            modified_timeline.append({"startTime":obj.timeline[i*2], "endTime":obj.timeline[i*2+1]})
        return modified_timeline


class FaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Face
        fields = ('id', 'url', 'face_img_url', 'face_group', 'face_rect', "selected", 'created_on', 'modified_on')
        read_only_fields = ("id", "url", "face_img_url", "face_rect")


class HardCutsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HardCuts
        fields = ('id', 'url', 'video', 'cuts', 'created_on', 'modified_on')
