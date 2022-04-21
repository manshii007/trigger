from .models import VendorProgram, VendorCommercial, VendorPromo
import tqdm
from django.contrib.postgres.search import TrigramSimilarity


def similar_commercials():
    qs = VendorCommercial.objects.all().filter(is_mapped=False)
    for instance in tqdm.tqdm(qs):
        vc = VendorCommercial.objects.filter(is_mapped=False).exclude(id=instance.id, vendor=instance.vendor) \
            .filter(brand_sector=instance.brand_sector, brand_category=instance.brand_category,
                    advertiser=instance.advertiser,).filter(descriptor__trigram_similar=instance.descriptor,
                                                           title__trigram_similar=instance.title).first()
        if vc:
            instance.similars.add(vc)
            instance.save()


def similar_commercial(id):
    obj = VendorCommercial.objects.get(id=id)
    qs = VendorCommercial.objects.filter(is_mapped=False, similars=obj).distinct()
    for instance in tqdm.tqdm(qs):
        vc = VendorCommercial.objects.exclude(id=instance.id, is_mapped=False) \
            .filter(brand_sector=instance.brand_sector, brand_category=instance.brand_category,
                    advertiser=instance.advertiser).filter(descriptor__trigram_similar=instance.descriptor,
                                                           title__trigram_similar=instance.title).first()
        if vc:
            instance.similars.add(vc)
            instance.save()


def similar_promos():
    qs = VendorPromo.objects.all().filter(is_mapped=False)
    for instance in tqdm.tqdm(qs):
        vc = VendorPromo.objects.filter(is_mapped=False).exclude(id=instance.id, vendor=instance.vendor) \
            .filter(brand_sector=instance.brand_sector, brand_category=instance.brand_category,
                    advertiser=instance.advertiser).annotate(similarity=TrigramSimilarity('title', instance.title),).filter(similarity__gt=0.90).order_by('-similarity').first()
        if vc:
            instance.similars.add(vc)
            instance.save()


def similar_prgs():
    qs = VendorProgram.objects.all().filter(is_mapped=False)
    for instance in tqdm.tqdm(qs):
        vc = VendorProgram.objects.filter(is_mapped=False).exclude(id=instance.id, vendor=instance.vendor) \
            .filter(program_genre=instance.program_genre, channel=instance.channel).annotate(similarity=TrigramSimilarity('title', instance.title),).filter(similarity__gt=0.90).order_by('-similarity').first()
        if vc:
            instance.similars.add(vc)
            instance.save()


def similar_maps():
    similar_commercials()
    similar_promos()
    similar_prgs()


def similar_promo(id):
    obj = VendorPromo.objects.get(id=id)
    qs = VendorPromo.objects.all().filter(is_mapped=False,similars=obj).distinct()
    for instance in tqdm.tqdm(qs):
        vc = VendorPromo.objects.filter(is_mapped=False).exclude(id=instance.id) \
            .filter(brand_sector=instance.brand_sector, brand_category=instance.brand_category,
                    advertiser=instance.advertiser).filter(title__trigram_similar=instance.title).first()
        if vc:
            instance.similars.add(vc)
            instance.save()
