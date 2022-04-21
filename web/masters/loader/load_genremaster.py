from xml.etree import ElementTree
from masters.models import Vendor, VendorProgramGenre
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
            if vendor=="PFT":
                if not VendorProgramGenre.objects.filter(name=row_data[0], program_theme=row_data[2], vendor=ven) :
                    s = VendorProgramGenre(name=row_data[0], code=row_data[1],
                                           program_theme=row_data[2], program_theme_code=row_data[3],
                                           vendor=ven)
                    data.append(s)
            else:
                if not VendorProgramGenre.objects.filter(name=row_data[1], program_theme=row_data[3], vendor=ven) :
                    s = VendorProgramGenre(name=row_data[1], code=row_data[0],
                                           program_theme=row_data[3], program_theme_code=row_data[2],
                                           vendor=ven)
                    data.append(s)
        except TypeError:
            pass
        try:
            if len(data) % batch_size == 0:
                VendorProgramGenre.objects.bulk_create(data)
                data = []
        except IntegrityError:
            data = []
            pass

    VendorProgramGenre.objects.bulk_create(data)


