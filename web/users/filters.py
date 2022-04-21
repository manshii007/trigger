import django_filters

from .models import (
    User,
)

class UserWorkGroupFilter(django_filters.rest_framework.FilterSet):
    workgroup = django_filters.UUIDFilter(name="membership__workgroup__id")

    class Meta:
        model = User
        fields = ('workgroup',)