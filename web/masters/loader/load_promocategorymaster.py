from xml.etree import ElementTree
from masters.models import Vendor, VendorPromoCategory
from tags.models import Channel
from django.db.utils import IntegrityError
import tqdm


def load(file='./masters/data/TAM/Genremstxml_20190416.xml', vendor="TAM", loc=0):
    batch_size = 2000

    tree = ElementTree.parse(file)
    root = tree.getroot()
    data = []
    ven, c = Vendor.objects.get_or_create(name=vendor.upper())
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            if not VendorPromoCategory.objects.filter(name=row_data[0], vendor=ven) :
                s = VendorPromoCategory(name=row_data[0], code=row_data[1],
                                        vendor=ven)
                data.append(s)
        except TypeError:
            pass
        try:
            if len(data) % batch_size == 0:
                VendorPromoCategory.objects.bulk_create(data)
                data = []
        except IntegrityError:
            data = []
            pass

    VendorPromoCategory.objects.bulk_create(data)


