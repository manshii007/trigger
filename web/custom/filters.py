from django.contrib import admin
from django.db.models import Q


class InputFilter(admin.SimpleListFilter):
    template = 'admin/input_filter.html'

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice


class TriviaFilter(InputFilter):
    parameter_name = 'trivia'
    title = ('Trivia')

    def queryset(self, request, queryset):
        if self.value() is not None:
            trivia = self.value()
            return queryset.filter(
                Q(trivia__icontains=trivia)
            )


class ActorFilter(InputFilter):
    parameter_name = 'actor'
    title = ('Actor')

    def queryset(self, request, queryset):
        if self.value() is not None:
            actor = self.value()
            return queryset.filter(
                Q(actors__name__icontains=actor)
            )


class PersonFilter(InputFilter):
    parameter_name = 'person'
    title = ('Person')

    def queryset(self, request, queryset):
        if self.value() is not None:
            person = self.value()
            return queryset.filter(
                Q(persons__name__icontains=person)
            )


class SeriesFilter(InputFilter):
    parameter_name = 'series'
    title = ('Series')

    def queryset(self, request, queryset):
        if self.value() is not None:
            series = self.value()
            return queryset.filter(
                Q(series__series_title__icontains=series)
            )


class LanguageFilter(InputFilter):
    parameter_name = 'language'
    title = ('Language')

    def queryset(self, request, queryset):
        if self.value() is not None:
            lang = self.value()
            return queryset.filter(
                Q(language__icontains=lang)
            )


class ChannelFilter(InputFilter):
    parameter_name = 'channel'
    title = ('Channel')

    def queryset(self, request, queryset):
        if self.value() is not None:
            lang = self.value()
            return queryset.filter(
                Q(channel__channel_name__icontains=lang)
            )


class MovieFilter(InputFilter):
    parameter_name = 'movie'
    title = ('Movie')

    def queryset(self, request, queryset):
        if self.value() is not None:
            lang = self.value()
            return queryset.filter(
                Q(movie_title__icontains=lang)
            )


class MovieTitleFilter(InputFilter):
    parameter_name = 'movie_title'
    title = ('Movie')

    def queryset(self, request, queryset):
        if self.value() is not None:
            lang = self.value()
            return queryset.filter(
                Q(movie__movie_title__icontains=lang)
            )


class BrandTitleFilter(InputFilter):
    parameter_name = 'brand_title'
    title = ('Brand Title')

    def queryset(self, request, queryset):
        if self.value() is not None:
            lang = self.value()
            return queryset.filter(
                Q(brand_title__icontains=lang)
            )

class BrandSectorFilter(InputFilter):
    parameter_name = 'brand_sector'
    title = ('Brand Sector')

    def queryset(self, request, queryset):
        if self.value() is not None:
            lang = self.value()
            return queryset.filter(
                Q(brand_sector__icontains=lang)
            )


class BrandCategoryFilter(InputFilter):
    parameter_name = 'brand_category'
    title = ('Brand Category')

    def queryset(self, request, queryset):
        if self.value() is not None:
            lang = self.value()
            return queryset.filter(
                Q(brand_category__icontains=lang)
            )


class DescriptorFilter(InputFilter):
    parameter_name = 'descriptor'
    title = ('Descriptor')

    def queryset(self, request, queryset):
        if self.value() is not None:
            lang = self.value()
            return queryset.filter(
                Q(descriptor__icontains=lang)
            )


class AdvertiserFilter(InputFilter):
    parameter_name = 'advertiser'
    title = ('Advertiser')

    def queryset(self, request, queryset):
        if self.value() is not None:
            lang = self.value()
            return queryset.filter(
                Q(advertiser__icontains=lang)
            )


class AdvertiserGroupFilter(InputFilter):
    parameter_name = 'advertiser_group'
    title = ('Advertiser Group')

    def queryset(self, request, queryset):
        if self.value() is not None:
            lang = self.value()
            return queryset.filter(
                Q(advertiser_group__icontains=lang)
            )