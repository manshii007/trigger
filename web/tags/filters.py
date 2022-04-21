import django_filters
from django_filters.rest_framework import FilterSet

from .models import (
    Tag,
    TagCategory,
    FrameTag,
    SceneTag,
    KeywordTag,
    Promo,
    Program,
    Commercial,
    ManualTag,
    GenericTag
)

class GenericTagFilter(FilterSet):
    level = django_filters.CharFilter(name='level')
    title = django_filters.CharFilter(name='title')
    parent = django_filters.UUIDFilter(name="parent")
    parent_title = django_filters.CharFilter(name='parent__title')

    class Meta:
        model = GenericTag
        fields = ('level', 'title', 'parent', 'parent_title')

class TagFilter(FilterSet):
    category_name = django_filters.CharFilter(name='category__name')

    class Meta:
        model = Tag
        fields = ('name', 'category_name', 'category')


class TagCategoryFilter(FilterSet):
    class Meta:
        model = TagCategory
        fields = ('name',)

class FrameTagFilter(FilterSet):
    title = django_filters.CharFilter(name="tag__title")

    class Meta:
        model = FrameTag
        fields = ('title',)

class KeywordTagFilter(FilterSet):
    words = django_filters.CharFilter(name="words")

    class Meta:
        model = KeywordTag
        fields = ('words',)


class SceneTagFilter(FilterSet):
    series = django_filters.CharFilter(name="episode__series__series_title")
    episode_number = django_filters.NumberFilter(name="episode__episode_number")

    class Meta:
        model = SceneTag
        fields = ('series', 'episode_number')


class PlayoutTagFilter(FilterSet):
    channel = django_filters.UUIDFilter(name="video__channel_clip")


class ProgramFilter(FilterSet):
    title_name = django_filters.CharFilter(name="title__name")
    channel_name = django_filters.CharFilter(name="channel__name")
    channel_code = django_filters.NumberFilter(name="channel__code")

    class Meta:
        model = Program
        fields = {"title_name": ['icontains',],
                  "channel_name": ['exact', 'icontains', 'istartswith'],
                  "channel_code": ['exact'],
                  "created_on": ['exact']
                  }


class PromoFilter(FilterSet):
    title_name = django_filters.CharFilter(name="brand_name__name")
    descriptor_name = django_filters.CharFilter(name="descriptor__text")

    class Meta:
        model = Promo
        fields = {"title_name": ['icontains',],
                  "descriptor_name": ['exact', 'icontains', 'istartswith']
                  }


class CommercialFilter(FilterSet):
    title_name = django_filters.CharFilter(name="title__name")
    descriptor_name = django_filters.CharFilter(name="descriptor__text")

    class Meta:
        model = Commercial
        fields = {"title_name": ['icontains',],
                  "descriptor_name": ['exact', 'icontains', 'istartswith']
                  }

class ManualTagFilter(FilterSet):
    title = django_filters.CharFilter(name="tags__title")
    
    class Meta:
        model = ManualTag
        fields = ('title', 'video')