from xml.etree import ElementTree
from tags.models import Advertiser, AdvertiserGroup, BrandCategory, BrandName, BrandSector, Descriptor, Commercial
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
        comm = Commercial.objects.filter(id=row_data[14]).first()
        k = "{}".format(row_data[14])
        if not comm:
            # channel, title, language, theme, genre, prod house
            desc = Descriptor.objects.filter(text=row_data[12], code=row_data[13]).first()

            adgroup = AdvertiserGroup.objects.filter(name=row_data[10], code=row_data[11]).first()

            sector = BrandSector.objects.filter(name=row_data[4], code=row_data[5]).first()

            cat = BrandCategory.objects.filter(name=row_data[6], code=row_data[7]).first()

            ad = Advertiser.objects.filter(name=row_data[8], code=row_data[9], advertiser_group=adgroup).first()

            name = BrandName.objects.filter(name=row_data[0], code=row_data[1]).first()
            if Commercial.objects.filter(id=row_data[14]).first():
                c = Commercial.objects.filter(id=row_data[14]).first()
                c.brand_name = name
                c.descriptor = desc
                c.advertiser = ad
                c.save()
            elif k not in commercialskeys:
                commercials.append(Commercial(id=row_data[14], brand_name=name, advertiser=ad, descriptor=desc))
                commercialskeys.add(k)
    Commercial.objects.bulk_create(commercials, 2000)
    commercialskeys.clear()
    silentremove(tmp_file)
    print("------------------------------Done----------------------------------")