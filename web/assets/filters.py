from django_filters.rest_framework import FilterSet
import django_filters

from .models import RO


class ROFilterSet(FilterSet):
    created_on = django_filters.DateFilter(input_formats=['%Y-%m-%d','%d-%m-%Y'],lookup_expr='icontains')

    class Meta:
        model = RO
        fields = {"channel": ['exact', 'contains', 'icontains', 'istartswith'],
                  "object": ['exact', 'contains', 'icontains', 'istartswith'],
                  "dest": ['exact', 'contains', 'icontains', 'istartswith'],
                  "title": ['exact', 'contains', 'icontains', 'istartswith'],
                  "advertiser": ['exact', 'contains', 'icontains', 'istartswith'],
                  "brand": ['exact', 'contains', 'icontains', 'istartswith'],
                  "created_by":['exact'],
                  "created_on": ['exact']
                  }
