from xml.etree import ElementTree
from masters.models import Vendor, VendorCommercial
from tags.models import Commercial, Descriptor
from django.db.utils import IntegrityError
import tqdm


def load(file='./masters/data/TAM/BrandMstXml_20190416.xml', vendor="TAM"):
    batch_size = 2000

    tree = ElementTree.parse(file)
    root = tree.getroot()
    data = []
    ven, c = Vendor.objects.get_or_create(name=vendor.upper())
    vendor_data = VendorCommercial.objects.filter(vendor=ven).values("brand_name_code", "descriptor_code")
    vendor_keys = ["{}---{}".format(x['brand_name_code'], x["descriptor_code"]) for x in vendor_data]
    vendor_keys = set(vendor_keys)
    vendor_ids = VendorCommercial.objects.filter(vendor=ven).values_list("id", flat=True)
    master_data = Commercial.objects.all().values("brand_name__code", "descriptor__code")
    master_keys = ["{}---{}".format(x['brand_name__code'], x["descriptor__code"]) for x in master_data]
    master_keys = set(master_keys)
    master_ids = Commercial.objects.all().values_list("id", flat=True)
    all_ids = list(vendor_ids)
    all_ids = [str(x) for x in all_ids]
    ids_keys = set(all_ids)
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        child.clear()
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            check_key = "{}---{}".format(row_data[1], row_data[13])
            if len(row_data)==14:
                if check_key not in vendor_keys:
                    s = VendorCommercial(brand_name=row_data[0], brand_name_code=row_data[1], title=row_data[2],
                                         title_code=row_data[3], brand_sector=row_data[4], brand_sector_code=row_data[5],
                                         brand_category=row_data[6], brand_category_code=row_data[7], advertiser=row_data[8],
                                         advertiser_code=row_data[9], advertiser_group=row_data[10],
                                         advertiser_group_code=row_data[11], descriptor=row_data[12],
                                         descriptor_code=row_data[13],
                                         vendor=ven
                                         )
                    data.append(s)
            elif len(row_data)==15:
                if row_data[14] in master_data and check_key not in master_keys:
                    print(row_data)
                if row_data[14] not in ids_keys and row_data[4] and row_data[6]:
                    s = VendorCommercial(brand_name=row_data[0], brand_name_code=row_data[1], title=row_data[2],
                                         title_code=row_data[3], brand_sector=row_data[4],
                                         brand_sector_code=row_data[5],
                                         brand_category=row_data[6], brand_category_code=row_data[7],
                                         advertiser=row_data[8],
                                         advertiser_code=row_data[9], advertiser_group=row_data[10],
                                         advertiser_group_code=row_data[11], descriptor=row_data[12],
                                         descriptor_code=row_data[13],
                                         vendor=ven, id=row_data[14]
                                         )
                    data.append(s)
                elif row_data[14] in ids_keys and check_key not in vendor_keys:
                    vc_updated = VendorCommercial.objects.filter(id=row_data[14])
                    vc_updated.update(brand_name=row_data[0], brand_name_code=row_data[1], title=row_data[2],
                                      title_code=row_data[3], brand_sector=row_data[4],
                                      brand_sector_code=row_data[5],
                                      brand_category=row_data[6], brand_category_code=row_data[7],
                                      advertiser=row_data[8],
                                      advertiser_code=row_data[9], advertiser_group=row_data[10],
                                      advertiser_group_code=row_data[11], descriptor=row_data[12],
                                      descriptor_code=row_data[13],
                                      vendor=ven
                                      )
        except TypeError:
            print(row_data)
            pass
        try:
            if len(data) % batch_size == 0:
                VendorCommercial.objects.bulk_create(data)
                data = []
        except IntegrityError:
            data = []
            pass
    root.clear()
    VendorCommercial.objects.bulk_create(data)


def test_break(file, vendor):
    tree = ElementTree.parse(file)
    root = tree.getroot()
    data = []
    ven, c = Vendor.objects.get_or_create(name=vendor.upper())
    vendor_data = VendorCommercial.objects.filter(vendor=ven).values("brand_name_code", "descriptor_code")
    vendor_keys = ["{}---{}".format(x['brand_name_code'], x["descriptor_code"]) for x in vendor_data]
    vendor_keys = set(vendor_keys)
    vendor_ids = VendorCommercial.objects.filter(vendor=ven).values_list("id", flat=True)
    master_data = Commercial.objects.all().values("brand_name__code", "descriptor__code")
    master_keys = ["{}---{}".format(x['brand_name__code'], x["descriptor__code"]) for x in master_data]
    master_keys = set(master_keys)
    master_ids = Commercial.objects.all().values_list("id", flat=True)
    master_id_keys = set([str(x) for x in master_ids])
    all_ids = list(vendor_ids) + list(master_ids)
    all_ids = [str(x) for x in all_ids]
    ids_keys = set(all_ids)
    vendor_id_keys = set([str(x) for x in vendor_ids])
    count = [0]*9
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        child.clear()
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            check_key = "{}---{}".format(row_data[1], row_data[13])
            if len(row_data) == 15:
                if row_data[14] not in ids_keys:
                    count[0] +=1
                    s = VendorCommercial(brand_name=row_data[0], brand_name_code=row_data[1], title=row_data[2],
                                         title_code=row_data[3], brand_sector=row_data[4],
                                         brand_sector_code=row_data[5],
                                         brand_category=row_data[6], brand_category_code=row_data[7],
                                         advertiser=row_data[8],
                                         advertiser_code=row_data[9], advertiser_group=row_data[10],
                                         advertiser_group_code=row_data[11], descriptor=row_data[12],
                                         descriptor_code=row_data[13],
                                         vendor=ven, id=row_data[14]
                                         )
                    data.append(s)
                    # create new entries to be checked by the users
                elif row_data[14] in master_id_keys and row_data[14] not in vendor_id_keys:
                    count[1]+=1
                    # create new entries to be automatically assigned to supermaster with same id
                    m = Commercial.objects.get(id=row_data[14])
                    s = VendorCommercial(brand_name=row_data[0], brand_name_code=row_data[1], title=row_data[2],
                                         title_code=row_data[3], brand_sector=row_data[4],
                                         brand_sector_code=row_data[5],
                                         brand_category=row_data[6], brand_category_code=row_data[7],
                                         advertiser=row_data[8],
                                         advertiser_code=row_data[9], advertiser_group=row_data[10],
                                         advertiser_group_code=row_data[11], descriptor=row_data[12],
                                         descriptor_code=row_data[13],
                                         vendor=ven, id=row_data[14], is_mapped=True, commercial=m
                                         )
                    data.append(s)
                else:
                    if row_data[14] in vendor_id_keys:
                        count[2]+=1
                        if check_key not in vendor_keys:
                            count[3] +=1
                            vc_updated = VendorCommercial.objects.filter(id=row_data[14])
                            vc_updated.update(brand_name=row_data[0], brand_name_code=row_data[1], title=row_data[2],
                                              title_code=row_data[3], brand_sector=row_data[4],
                                              brand_sector_code=row_data[5],
                                              brand_category=row_data[6], brand_category_code=row_data[7],
                                              advertiser=row_data[8],
                                              advertiser_code=row_data[9], advertiser_group=row_data[10],
                                              advertiser_group_code=row_data[11], descriptor=row_data[12],
                                              descriptor_code=row_data[13],
                                              vendor=ven
                                              )
                count[4]+=1
        except TypeError:
            print(row_data)
            pass
        except:
            print(row_data)
            pass
    VendorCommercial.objects.bulk_create(data, 2000)
    print("Count : {}".format(count))