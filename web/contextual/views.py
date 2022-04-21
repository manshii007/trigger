from rest_framework import viewsets, permissions, filters
import django_filters
from .serializers import (
    FaceGroupSerializer,
    UpdateFaceGroupSerializer,
    FaceSerializer,
    HardCutsSerializer
)
from .models import (
    Face,
    FaceGroup,
    HardCuts
)
from pagination.pagination import StandardResultsSetPagination


class FaceViewSet(viewsets.ModelViewSet):
    serializer_class = FaceSerializer
    queryset = Face.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("face_group__person", "face_group", "selected")
    search_fields = ("face_group__person__name", "face_group__video__title")


class FaceGroupViewSet(viewsets.ModelViewSet):
    serializer_class = FaceGroupSerializer
    queryset = FaceGroup.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = StandardResultsSetPagination
    action_serializer_classes = {
        "update": UpdateFaceGroupSerializer
    }
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("person",)
    search_fields = ("person__name", "video__title")

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(FaceGroupViewSet, self).get_serializer_class()


class HardCutsViewSet(viewsets.ModelViewSet):
    serializer_class = HardCutsSerializer
    queryset = HardCuts.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
