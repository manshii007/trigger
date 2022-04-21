from xml.etree import ElementTree
from tags.models import Advertiser, AdvertiserGroup, BrandCategory, BrandName, BrandSector, Descriptor, Commercial
from django.db.utils import IntegrityError
import tqdm


def load(file='./masters/data/TAM/BrandMstXml_20190416.xml'):
    tree = ElementTree.parse(file)
    root = tree.getroot()
    data = []
    adgroups= []
    sectors = []
    des = []
    adgroupskeys = set()
    sectorskeys = set()
    deskeys = set()
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        data.append(row_data)
    for row_data in tqdm.tqdm(data):
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            adgroup = AdvertiserGroup.objects.filter(name=row_data[10], code=row_data[11]).first()
            if not adgroup and row_data[10] and row_data[10] not in adgroupskeys:
                adgroups.append(AdvertiserGroup(name=row_data[10], code=row_data[11]))
                adgroupskeys.add(row_data[10])

            sector = BrandSector.objects.filter(name=row_data[4], code=row_data[5]).first()
            if not sector and row_data[4] and row_data[4] not in sectorskeys:
                sectors.append(BrandSector(name=row_data[4], code=row_data[5]))
                sectorskeys.add(row_data[4])

            desc = Descriptor.objects.filter(text=row_data[12], code=row_data[13]).first()
            if not desc :
                if row_data[12] and row_data[12] not in deskeys:
                    des.append(Descriptor(text=row_data[12], code=row_data[13]))
                    deskeys.add(row_data[12])
        except TypeError:
            pass
    BrandSector.objects.bulk_create(sectors,2000)
    AdvertiserGroup.objects.bulk_create(adgroups,2000)
    Descriptor.objects.bulk_create(des, 2000)
    deskeys.clear()
    adgroupskeys.clear()
    sectorskeys.clear()
    print("------------------------------STEP 1----------------------------------")
    ads = []
    cats = []
    adskeys = set()
    catskeys = set()
    for row_data in tqdm.tqdm(data):
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            adgroup = AdvertiserGroup.objects.filter(name=row_data[10]).first()
            ad = Advertiser.objects.filter(name=row_data[8], code=row_data[9]).first()
            if not ad:
                if row_data[8] and row_data[8] not in adskeys:
                    ads.append(Advertiser(name=row_data[8], code=row_data[9], advertiser_group=adgroup))
                    adskeys.add(row_data[8])
            sector = BrandSector.objects.filter(name=row_data[4], code=row_data[5]).first()
            cat = BrandCategory.objects.filter(name=row_data[6], code=row_data[7]).first()
            if not cat:
                if row_data[6] and row_data[6] not in catskeys:
                    cats.append(BrandCategory(name=row_data[6], code=row_data[7], brand_sector=sector))
                    catskeys.add(row_data[6])
        except TypeError:
            pass

    BrandCategory.objects.bulk_create(cats, 2000)
    Advertiser.objects.bulk_create(ads, 2000)
    adskeys.clear()
    catskeys.clear()
    print("------------------------------STEP 2----------------------------------")
    names = []
    nameskeys = set()
    for row_data in tqdm.tqdm(data):
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            cat = BrandCategory.objects.filter(name=row_data[6], code=row_data[7]).first()
            name = BrandName.objects.filter(name=row_data[0], code=row_data[1]).first()
            if not name:
                if row_data[0] and row_data[0] not in nameskeys:
                    names.append(BrandName(name=row_data[0], code=row_data[1], brand_category=cat))
                    nameskeys.add(row_data[0])
        except TypeError:
            pass

    BrandName.objects.bulk_create(names, 2000)
    nameskeys.clear()
    print("------------------------------STEP 3----------------------------------")
    commercials = []
    commercialskeys = set()
    for row_data in tqdm.tqdm(data):
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            desc = Descriptor.objects.filter(text=row_data[12], code=row_data[13]).first()
            ad = Advertiser.objects.filter(name=row_data[8], code=row_data[9]).first()
            name = BrandName.objects.filter(name=row_data[0], code=row_data[1]).first()
            comm = Commercial.objects.filter(brand_name=name, descriptor=desc)
            k = "{}----{}".format(row_data[0], row_data[12])
            if not comm :
                if desc and name :
                    if k not in commercialskeys:
                        commercials.append(Commercial(id=row_data[14], brand_name=name, advertiser=ad, descriptor=desc))
                        commercialskeys.add(k)
        except TypeError:
            pass
    Commercial.objects.bulk_create(commercials, 2000)
    commercialskeys.clear()
    print("------------------------------Done----------------------------------")