from masters.models import VendorPromo
from tags.models import *
import tqdm


def correct():
    vcgs = VendorPromo.objects.all().filter(promo__isnull=True, is_mapped=True)
    for vc in tqdm.tqdm(vcgs):
        brand_sector = BrandSector.objects.filter(name=vc.brand_sector).first()
        if not brand_sector and vc.brand_sector:
            brand_sector = BrandSector.objects.create(name=vc.brand_sector)
        brand_category = BrandCategory.objects.filter(name=vc.brand_category, brand_sector=brand_sector).first()
        if not brand_category and vc.brand_category:
            brand_category = BrandCategory.objects.create(name=vc.brand_category, brand_sector=brand_sector)
        brand_name = BrandName.objects.filter(name=vc.brand_name, brand_category=brand_category).first()
        if not brand_name and vc.brand_name:
            brand_name = BrandName.objects.create(name=vc.brand_name, brand_category=brand_category)
        advertiser_group = AdvertiserGroup.objects.filter(name=vc.advertiser_group).first()
        if not advertiser_group and vc.advertiser_group:
            advertiser_group = AdvertiserGroup.objects.create(name=vc.advertiser_group)
        advertiser = Advertiser.objects.filter(name=vc.advertiser, advertiser_group=advertiser_group).first()
        if not advertiser and vc.advertiser:
            advertiser = Advertiser.objects.create(name=vc.advertiser, advertiser_group=advertiser_group)

        if vc.descriptor and brand_name:
            descriptor = Descriptor.objects.filter(text=vc.descriptor).first()
            if not descriptor:
                descriptor = Descriptor.objects.create(text=vc.descriptor)
            super_promo = Promo.objects.filter(title=None, brand_name=brand_name,
                                               advertiser=advertiser, descriptor=descriptor, deleted=False).first()
            if not super_promo:
                super_promo = Promo.objects.create(title=None, brand_name=brand_name, advertiser=advertiser,
                                                   descriptor=descriptor, deleted=False)
            vc.promo = super_promo
            vc.is_mapped = True
            vc.save()
        elif brand_name:
            descriptor = Descriptor.objects.get(text="THEME NOT MONITORED")
            super_promo = Promo.objects.filter(title=None, brand_name=brand_name,
                                               advertiser=advertiser, descriptor=descriptor, deleted=False).first()
            if not super_promo:
                super_promo = Promo.objects.create(title=None, brand_name=brand_name, advertiser=advertiser,
                                                   descriptor=descriptor, deleted=False)
            vc.promo = super_promo
            vc.is_mapped = True
            vc.save()