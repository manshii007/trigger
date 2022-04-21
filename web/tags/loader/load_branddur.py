from xml.etree import ElementTree
from masters.models import Vendor, VendorCommercial, VendorProgram, VendorPromo, VendorReportCommercial, \
    VendorReportPromo, Channel
# from django.db.utils import IntegrityError
import math, datetime
import glob, os, tqdm


def tcr2sec(tcr):

    h = int(tcr.split(":")[0])
    m = int(tcr.split(":")[1])
    s = int(tcr.split(":")[2])
    return int(h*3600+m*60+s)


def date2date(d):
    dt = datetime.datetime.strptime(d,"%d/%m/%Y")
    return dt.strftime("%Y-%m-%d")


def load(file='/tmp/Zee_TV_18-04-19.xml', vendor="TABSONS"):

    tree = ElementTree.parse(file)
    root = tree.getroot()
    ven, c = Vendor.objects.get_or_create(name=vendor.upper())
    vrcs = []
    vrps = []
    for child in root:
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        # print(row_data)
        channel = Channel.objects.filter(code=int(row_data[3])).first()
        if not channel:
            break
        if row_data[1] == "Commercial":
            dur = tcr2sec(row_data[14])
            vc = VendorCommercial.objects.filter(title=row_data[7], descriptor_code=row_data[15], vendor=ven).first()
            if vc:
                # if vc.durations:
                #     if dur not in vc.durations:
                #         vc.durations.append(dur)
                # else:
                #     vc.durations = [dur]
                # vc.save()

                vrc = VendorReportCommercial(date=date2date(row_data[10]), channel=channel, vendor=ven, commercial=vc,
                                             start_time=row_data[12], end_time=row_data[13], duration=dur)
                vrcs.append(vrc)
            if len(vrcs) > 500:
                VendorReportCommercial.objects.bulk_create(vrcs)
                vrcs = []

        if row_data[1] == "Promo":
            dur = tcr2sec(row_data[14])
            vc = VendorPromo.objects.filter(title=row_data[7], vendor=ven).first()
            if vc:
                # if vc.durations:
                #     if dur not in vc.durations:
                #         vc.durations.append(dur)
                # else:
                #     vc.durations = [dur]
                # vc.save()
                vrp = VendorReportPromo(date=date2date(row_data[10]), channel=channel, vendor=ven, promo=vc,
                                        start_time=row_data[12], end_time=row_data[13], duration=dur)
                vrps.append(vrp)
            if len(vrps) > 500:
                VendorReportPromo.objects.bulk_create(vrps)
                vrps = []
    VendorReportCommercial.objects.bulk_create(vrcs)
    VendorReportPromo.objects.bulk_create(vrps)


def load_dir(path=None, vendor="PFT"):

    for f in tqdm.tqdm(glob.glob(os.path.join(path, '*.xml'))):
        load(f, vendor)


if __name__ == '__main__':
    load()
