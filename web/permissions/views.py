#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.contrib.auth.models import (
    Permission
)

from rest_framework import (
    viewsets,
    permissions
)

from rest_framework_extensions.mixins import (
    CacheResponseMixin
)

from .serializers import (
    PermissionSerializer
)

from rest_framework import filters

class PermissionsViewSet(CacheResponseMixin,
                         viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name","content_type__model")
