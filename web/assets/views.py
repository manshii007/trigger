from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import filters
from rest_framework.decorators import detail_route, list_route
from .models import RO
from .serializers import ROSerializer, DetailROSerializer
import uuid
from django.conf import settings
from datetime import timedelta, datetime
from azure.storage.blob import (
    BlockBlobService,
    BlobPermissions
)
import django_filters
from .filters import ROFilterSet


class ROViewSet(ModelViewSet):
    queryset = RO.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_class = ROFilterSet
    search_fields = ("object", "dest", "channel", "title")
    serializer_class = ROSerializer
    action_serializer_classes = {
        "create": ROSerializer,
        "retrieve": DetailROSerializer,
        "update": ROSerializer,
        "list": DetailROSerializer
    }

    def generate_blob_sas(self, ext):
        block_blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME, account_key=settings.AZURE_ACCOUNT_KEY)
        video_name = "{}.{}".format(uuid.uuid4(), ext)
        block_blob_service.create_blob_from_bytes(settings.AZURE_CONTAINER, video_name, b'')
        token = block_blob_service.generate_blob_shared_access_signature(settings.AZURE_CONTAINER, video_name,
                                                                         BlobPermissions.WRITE,
                                                                         datetime.utcnow() + timedelta(hours=1))
        full_path = "https://" + settings.AZURE_ACCOUNT_NAME + ".blob.core.windows.net/" + settings.AZURE_CONTAINER + \
                    "/" + video_name
        return [full_path, token]

    @list_route(methods=['get'])
    def get_ro_url(self, request):
        ext = request.query_params.get('ext', 'pdf')
        blob_url, token = self.generate_blob_sas(ext)
        return Response(data={"blob_url": blob_url, "token": token})

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        print(datetime.now().time())
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(ROViewSet, self).get_serializer_class()

    @list_route(methods=['get'])
    def advertisers(self, request):
        qs = self.get_queryset()
        search = request.query_params.get("search","")
        advertisers = qs.filter(advertiser__icontains=search).values('advertiser').distinct()
        data = []
        for ad in advertisers:
            data.append(ad['advertiser'])
        return Response(data=data)
