from xml.etree import ElementTree
from masters.models import Vendor, VendorChannel
from tags.models import Channel
from django.db.utils import IntegrityError
import tqdm


def load(file='./masters/data/TAM/ChnMstXml_20190416.xml', vendor="TAM", loc=0):
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
            if not VendorChannel.objects.filter(name=row_data[0], vendor=ven) :
                s = VendorChannel(name=row_data[0], code=row_data[1], network_name=row_data[2],
                                  network_name_code=row_data[3], language=row_data[4], language_code=row_data[5],
                                  region=row_data[6], region_code=row_data[7], genre=row_data[8],
                                  genre_code=row_data[9],
                                  vendor=ven
                                  )
                data.append(s)
        except TypeError as e:
            raise e
        try:
            if len(data) % batch_size == 0:
                VendorChannel.objects.bulk_create(data)
                data = []
        except IntegrityError:
            data = []
            pass

    VendorChannel.objects.bulk_create(data)


