from xml.etree import ElementTree
from tags.models import Advertiser, AdvertiserGroup, BrandCategory, BrandName, BrandSector, Descriptor, Promo
import tqdm
from tags.loader.loader import clean_file, silentremove


def load(file):
    tmp_file = clean_file(file, True)
    tree = ElementTree.parse(tmp_file)
    root = tree.getroot()
    data = []

    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        data.append(row_data)
    print("Number of entries : {}".format(len(data)))
    ind = 0
    commercials = []
    commercialskeys = set()
    for row_data in tqdm.tqdm(data):
        ind +=1
        # channel, title, language, theme, genre, prod house
        comm = Promo.objects.filter(id=row_data[14]).first()
        k = row_data[14]
        if not comm:
            desc = Descriptor.objects.filter(text=row_data[12], code=row_data[13]).first()
            if not desc and row_data[12]:
                if Descriptor.objects.filter(text=row_data[12]).first():
                    a = Descriptor.objects.filter(text=row_data[12]).first()
                    a.code = row_data[13]
                    a.save()
                    desc = a
                else:
                    desc = Descriptor.objects.create(text=row_data[12], code=row_data[13])
            adgroup = AdvertiserGroup.objects.filter(name=row_data[10], code=row_data[11]).first()
            if not adgroup and row_data[11]:
                adgroup = AdvertiserGroup.objects.create(name=row_data[10] if row_data[10] else '', code=row_data[11])
            sector = BrandSector.objects.filter(name=row_data[4], code=row_data[5]).first()
            if not sector:
                sector = BrandSector.objects.create(name=row_data[4], code=row_data[5])
            cat = BrandCategory.objects.filter(name=row_data[6], code=row_data[7]).first()
            if not cat:
                if BrandCategory.objects.filter(name=row_data[6]).first():
                    a = BrandCategory.objects.filter(name=row_data[6]).first()
                    a.code = row_data[7]
                    a.brand_sector = sector
                    a.save()
                    cat = a
                else:
                    cat = BrandCategory.objects.create(name=row_data[6], code=row_data[7], brand_sector=sector)
            ad = Advertiser.objects.filter(name=row_data[8], code=row_data[9], advertiser_group=adgroup).first()
            if not ad:
                if Advertiser.objects.filter(name=row_data[8], advertiser_group=adgroup).first():
                    a = Advertiser.objects.filter(name=row_data[8]).first()
                    a.code = row_data[9]
                    a.advertiser_group = adgroup
                    a.save()
                    ad = a
                else:
                    ad = Advertiser.objects.create(name=row_data[8], code=row_data[9], advertiser_group=adgroup)
            name = BrandName.objects.filter(name=row_data[0], code=row_data[1]).first()
            if not name:
                if BrandName.objects.filter(name=row_data[0]).first():
                    a = BrandName.objects.filter(name=row_data[0]).first()
                    a.code = row_data[1]
                    a.brand_category = cat
                    a.save()
                    name = a
                else:
                    name = BrandName.objects.create(name=row_data[0], code=row_data[1], brand_category=cat)
            if Promo.objects.filter(id=row_data[14]).first():
                c = Promo.objects.filter(id=row_data[14]).first()
                c.brand_name = name
                c.descriptor = desc
                c.advertiser = ad
                c.save()
            elif k not in commercialskeys:
                commercials.append(Promo(id=row_data[14], brand_name=name, advertiser=ad, descriptor=desc))
                commercialskeys.add(k)
    Promo.objects.bulk_create(commercials, 2000)
    commercialskeys.clear()
    silentremove(tmp_file)
    print("------------------------------Done----------------------------------")