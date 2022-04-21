from xml.etree import ElementTree
from tags.models import PromoCategory
from django.db.utils import IntegrityError
import tqdm


def load(file='./masters/data/TAM/Genremstxml_20190416.xml',):
    batch_size = 2000

    tree = ElementTree.parse(file)
    root = tree.getroot()
    data = []
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            if not PromoCategory.objects.filter(name=row_data[0], code=row_data[1]) :
                s = PromoCategory(name=row_data[0], code=row_data[1], id=row_data[2])
                data.append(s)
        except TypeError:
            pass
        try:
            if len(data) % batch_size == 0:
                PromoCategory.objects.bulk_create(data)
                data = []
        except IntegrityError:
            data = []
            pass
    PromoCategory.objects.bulk_create(data)


