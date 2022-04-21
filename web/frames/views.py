from rest_framework import viewsets, permissions, status, views, generics, parsers, filters
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from tags.models import Tag
from .models import Rect, Frames, VideoFrame, PersonFrame
from django.core.exceptions import ObjectDoesNotExist
from .serializers import FramesSerializer, RectSerializer, \
    MildRectSerializer, VideoFrameSerializer, PersonFrameSerializer
from tags.serializers import TagSerializer
import uuid
from azure.storage.blob import (
    BlockBlobService,
    BlobPermissions
)
from .filters import PersonFrameFilter
from datetime import datetime, timedelta
from django.conf import settings
import django_filters


class CreateListModelMixin(object):

    def get_serializer(self, *args, **kwargs):
        """ if an array is passed, set serializer to many """
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super(CreateListModelMixin, self).get_serializer(*args, **kwargs)


class RectViewSet(viewsets.ModelViewSet):
    serializer_class = RectSerializer
    queryset = Rect.objects.all()

    @detail_route(methods=['get'])
    def tags(self, request, pk=None):
        rect = self.get_object()
        tags = rect.tags.all()
        tag_serializer = TagSerializer(tags, context={'request':request}, many=True)
        return Response(tag_serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def update_tags(self, request, pk=None):
        rect = self.get_object()
        rect.tags.clear()
        for tag_id in request.data["tags"]:
            tag_obj = Tag.objects.get(pk=tag_id)
            rect.tags.add(tag_obj)
        rect_serializer = RectSerializer(rect, context={"request": request})
        return Response(rect_serializer.data, status=status.HTTP_201_CREATED)


class FramesViewSet(viewsets.ModelViewSet):
    serializer_class = FramesSerializer
    queryset = Frames.objects.all()

    @detail_route(methods=['post'])
    def update_rects(self, request, pk=None):
        frame = self.get_object()
        frame.rects.all().delete()
        for rect in request.data["rects"]:
            try:
                rect_obj = Rect.objects.get(pk=rect['id'])
            except ObjectDoesNotExist:
                rect_obj = None
            if rect_obj:
                rect_obj.x = rect['x']
                rect_obj.y = rect['y']
                rect_obj.w = rect['w']
                rect_obj.h = rect['h']
                rect_obj.tags.clear()
                for tag in rect['tags']:
                    tag_obj = Tag.objects.get(pk=tag['id'])
                    rect_obj.tags.add(tag_obj)
                rect_obj.save()
            else:
                rect_obj = Rect(x=rect['x'],
                                y=rect['y'],
                                w=rect['w'],
                                h=rect['h'],
                                id=rect['id'],
                                frame=frame)
                rect_obj.save()
                for tag in rect['tags']:
                    tag_obj = Tag.objects.get(pk=tag['id'])
                    rect_obj.tags.add(tag_obj)
                rect_obj.save()
        frame_data = FramesSerializer(frame, context={'request': request})
        return Response(frame_data.data, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def get_frame_url(self, request):
        blob_url, token = self.generate_blob_sas()
        return Response(data={"blob_url": blob_url, "token": token})

    def generate_blob_sas(self):
        block_blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME, account_key=settings.AZURE_ACCOUNT_KEY)
        video_name = "{}.{}".format(uuid.uuid4(), 'png')
        block_blob_service.create_blob_from_bytes(settings.AZURE_CONTAINER, video_name, b'')
        token = block_blob_service.generate_blob_shared_access_signature(settings.AZURE_CONTAINER, video_name,
                                                                         BlobPermissions.WRITE,
                                                                         datetime.utcnow() + timedelta(hours=1))
        full_path = "https://" + settings.AZURE_ACCOUNT_NAME + ".blob.core.windows.net/" + settings.AZURE_CONTAINER + \
                    "/" + video_name
        return [full_path, token]


class VideoFrameViewSet(viewsets.ModelViewSet):
    serializer_class = VideoFrameSerializer
    queryset = VideoFrame.objects.all()
    permission_classes = (permissions.IsAuthenticated,)


class PersonFrameViewSet(CreateListModelMixin, viewsets.ModelViewSet):
    serializer_class = PersonFrameSerializer
    queryset = PersonFrame.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = PersonFrameFilter
    search_fields = ('person__name',)
