from xml.etree import ElementTree
from masters.models import Vendor, VendorProgram
from tags.models import Channel, Program
from django.db.utils import IntegrityError
import tqdm


def load(file='./masters/data/TAM/PrmMstXml_20190416.xml', vendor="TAM", loc=0):
    batch_size = 2000

    tree = ElementTree.parse(file)
    root = tree.getroot()
    data = []
    ven, c = Vendor.objects.get_or_create(name=vendor.upper())
    vt = VendorProgram.objects.filter(vendor=ven).values("channel__code", "title_code")
    vt_ids = VendorProgram.objects.filter(vendor=ven).values_list("id", flat=True)
    vt_keys = [str(x) for x in vt_ids]
    vt_keys = set(vt_keys)
    keys = ["{}---{}".format(x['channel__code'], x["title_code"]) for x in vt ]
    keys = set(keys)
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        child.clear()
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            check_key = "{}---{}".format(row_data[loc], row_data[3])
            if len(row_data) >=11 and len(row_data)<13:
                if check_key not in keys:
                    ch = Channel.objects.filter(code=int(row_data[loc])).first()
                    s = VendorProgram(title=row_data[2], title_code=row_data[3], language=row_data[4], language_code=row_data[5],
                                      program_theme=row_data[6], program_theme_code=row_data[7], program_genre=row_data[8],
                                      program_genre_code=row_data[9], prod_house=row_data[10],
                                      prod_house_code=row_data[11],
                                      vendor=ven, channel=ch
                                      )
                    data.append(s)
            elif len(row_data)==10:
                if check_key not in keys:
                    ch = Channel.objects.filter(code=int(row_data[loc])).first()
                    s = VendorProgram(title=row_data[2], title_code=row_data[3], language=row_data[4],
                                      language_code=row_data[5],
                                      program_theme=row_data[6], program_theme_code=row_data[7],
                                      program_genre=row_data[8],
                                      program_genre_code=row_data[9],
                                      vendor=ven, channel=ch
                                      )
                    data.append(s)
            elif len(row_data) == 13:
                if row_data[12] not in vt_keys and check_key not in keys:
                    ch = Channel.objects.filter(code=int(row_data[loc])).first()
                    s = VendorProgram(title=row_data[2], title_code=row_data[3], language=row_data[4],
                                      language_code=row_data[5],
                                      program_theme=row_data[6], program_theme_code=row_data[7],
                                      program_genre=row_data[8],
                                      program_genre_code=row_data[9], prod_house=row_data[10],
                                      prod_house_code=row_data[11],
                                      vendor=ven, channel=ch, id=row_data[12]
                                      )
                    data.append(s)

        except TypeError:
            print(row_data)
            pass
        try:
            if len(data) % batch_size == 0:
                VendorProgram.objects.bulk_create(data)
                data = []
        except IntegrityError:
            data = []
            pass
    root.clear()
    VendorProgram.objects.bulk_create(data)


