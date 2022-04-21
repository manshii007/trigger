from rest_framework import serializers
from .models import Rect, Frames, VideoFrame, PersonFrame
from tags.models import Tag


class MildTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name')


class RectSerializer(serializers.ModelSerializer):
    tags = serializers.SlugRelatedField(slug_field='name',
                                        read_only=True,
                                        many=True)

    class Meta:
        model = Rect
        fields = ("id", 'url', "x", "y", "w", "h", "frame", 'tags')


class MildRectSerializer(serializers.ModelSerializer):
    tags = MildTagSerializer(many=True, read_only=True)

    class Meta:
        model = Rect
        fields = ("x", "y", "w", "h", "id", 'tags')


class FramesSerializer(serializers.ModelSerializer):
    rects = MildRectSerializer(many=True, read_only=True)

    class Meta:
        model = Frames
        fields = ("id", 'url', "file", 'rects')


class VideoFrameSerializer(serializers.ModelSerializer):
    file = serializers.URLField(source='frame.file')

    class Meta:
        model = VideoFrame
        fields = ("url", "file", "video")


class PersonFrameSerializer(serializers.ModelSerializer):
    file = serializers.URLField(source='frame.file')

    class Meta:
        model = PersonFrame
        fields = ("id", "url", "file", "person")
        read_only_fields = ("id", "url")

    def create(self, validated_data):
        frame_data = validated_data.pop("frame")
        frame_obj = Frames.objects.create(**frame_data)
        person_frame_obj = PersonFrame.objects.create(frame=frame_obj, **validated_data)
        return person_frame_obj
