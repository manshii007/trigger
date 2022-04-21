from lxml import etree as ElementTree
from masters.models import Vendor, VendorPromo
from tags.models import Promo
from django.db.utils import IntegrityError
import tqdm


def load(file='./masters/data/TAM/PromoMstXml_20190416.xml', vendor="TAM"):
    batch_size = 2000
    parser = ElementTree.XMLParser(recover=True)
    tree = ElementTree.parse(file, parser=parser)
    root = tree.getroot()
    data = []
    ven, c = Vendor.objects.get_or_create(name=vendor.upper())
    vendor_titles = VendorPromo.objects.filter(vendor=ven).values_list("title_code", flat=True)
    title_keys = set(vendor_titles)
    vendor_ids = VendorPromo.objects.filter(vendor=ven).values_list("id", flat=True)
    master_ids = Promo.objects.all().values_list("id", flat=True)
    all_ids = list(vendor_ids) + list(master_ids)
    all_ids = [str(x) for x in all_ids]
    ids_keys = set(all_ids)
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        child.clear()
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            check_key = "{}".format(row_data[3])
            if len(row_data)==14:
                if check_key not in title_keys:
                    s = VendorPromo(brand_name=row_data[0], brand_name_code=row_data[1], title=row_data[2],
                                    title_code=row_data[3], brand_sector=row_data[4], brand_sector_code=row_data[5],
                                    brand_category=row_data[6], brand_category_code=row_data[7], advertiser=row_data[8],
                                    advertiser_code=row_data[9], advertiser_group=row_data[10],
                                    advertiser_group_code=row_data[11], descriptor=row_data[12],
                                    descriptor_code=row_data[13],
                                    vendor=ven
                                    )
                    data.append(s)
            elif len(row_data)==15:
                if row_data[14] not in ids_keys:
                    s = VendorPromo(brand_name=row_data[0], brand_name_code=row_data[1], title=row_data[2],
                                    title_code=row_data[3], brand_sector=row_data[4], brand_sector_code=row_data[5],
                                    brand_category=row_data[6], brand_category_code=row_data[7], advertiser=row_data[8],
                                    advertiser_code=row_data[9], advertiser_group=row_data[10],
                                    advertiser_group_code=row_data[11], descriptor=row_data[12],
                                    descriptor_code=row_data[13],
                                    vendor=ven, id=row_data[14]
                                    )
                    data.append(s)
        except TypeError:
            print(row_data)
            pass
        try:
            if len(data) % batch_size == 0:
                VendorPromo.objects.bulk_create(data)
                data = []
        except IntegrityError:
            data = []
            pass
    root.clear()
    VendorPromo.objects.bulk_create(data)


