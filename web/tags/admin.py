#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.contrib import admin
from admin import admin_site
from .models import (
    Tag,
    TagCategory,
    FrameTag,
    BarcTag,
    CommercialTag,
    ProgramTheme,
    ProgramGenre,
    Commercial,
    Promo,
    Program,
    Advertiser,
    AdvertiserGroup,
    BrandName,
    BrandCategory,
    BrandSector,
    ContentLanguage,
    Descriptor,
    GenericTag
)
from custom.filters import (
    BrandCategoryFilter,
    BrandSectorFilter,
    BrandTitleFilter,
    AdvertiserFilter,
    AdvertiserGroupFilter,
    DescriptorFilter
)

admin.site.register(Tag)
admin.site.register(TagCategory)
admin.site.register(FrameTag)
admin.site.register(BarcTag)
admin_site.register(Tag)
admin_site.register(TagCategory)
admin_site.register(FrameTag)
admin.site.register(Descriptor)
admin.site.register(ProgramGenre)
admin.site.register(ProgramTheme)
admin.site.register(Program)
admin.site.register(Promo)
admin.site.register(Commercial)
admin.site.register(AdvertiserGroup)
admin.site.register(Advertiser)
admin.site.register(BrandSector)
admin.site.register(BrandCategory)
admin.site.register(BrandName)
admin.site.register(ContentLanguage)
admin.site.register(GenericTag)

@admin.register(CommercialTag)
class CommercialTagAdmin(admin.ModelAdmin):
    list_display = ('brand_title', 'brand_sector', 'brand_category', 'descriptor', "advertiser", "advertiser_group")
    fields = ('id', 'brand_title', 'brand_sector', 'brand_category', 'descriptor', 'advertiser', 'advertiser_group',
              'telecast_duration', 'content_language', 'video', 'video_player')
    search_fields = ("brand_title", "brand_category", "brand_sector", "descriptor", "advertiser", "advertiser_group")
    list_filter = (BrandTitleFilter, BrandSectorFilter, BrandCategoryFilter, AdvertiserGroupFilter, AdvertiserFilter, DescriptorFilter)
    readonly_fields = ('id', 'video', 'video_player')


admin_site.register(CommercialTag, CommercialTagAdmin)
