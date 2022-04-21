import django_filters

from .models import MovieTranslationJob, EpisodeTranslationJob, ReviewTranslationJob

#
# class MovieTranslationJobFilter(django_filters.rest_framework.FilterSet):
#     name = django_filters.CharFilter(name="person__name")
#
#     class Meta:
#         model = PersonFrame
#         fields = ('name',)