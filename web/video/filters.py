import django_filters

from .models import Video


class VideoFilter(django_filters.rest_framework.FilterSet):
    tags = django_filters.CharFilter(name="frametag__tag__name")

    class Meta:
        model = Video
        fields = {
            'title':['exact', 'contains', 'icontains', 'istartswith'],
            'tags':['exact', 'contains', 'icontains', 'istartswith']
        }