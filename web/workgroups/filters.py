import django_filters

from .models import (
    WorkGroup,
    Group
)


class WorkGroupFilter(django_filters.rest_framework.FilterSet):
    member = django_filters.CharFilter(name="group__user__id")

    class Meta:
        model = WorkGroup
        fields = ('name', 'member', 'organization')


class GroupFilter(django_filters.rest_framework.FilterSet):
    member = django_filters.CharFilter(name="user__username")

    class Meta:
        model = Group
        fields = ('name','member')
