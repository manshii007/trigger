
from __future__ import absolute_import, unicode_literals
from celery import Celery
from .models import VendorMasterComparison, VendorCommercial, VendorPromo, VendorProgram, MasterReport, \
    VendorProgramGenre, VendorContentLanguage, VendorPromoCategory, VendorChannel, SuperMaster
import boto3
from django.db.models import Count, Q
from functools import reduce
import operator, math, glob, json
from celery import chord
from tags.models import Channel
import os, tqdm
from botocore.exceptions import ClientError
import logging
import urllib
import subprocess as sp
from django.core.mail import send_mail
from video.tasks import check_or_create_file
from masters.loader.loader import load_base, load_prgmaster, load_promomaster
from xml.etree import ElementTree
from masters.models import Vendor, VendorCommercial, VendorProgram, VendorPromo, VendorReportCommercial, \
    VendorReportPromo, VendorReportProgram

import datetime
from tags.models import (
    BrandName,
    BrandCategory,
    BrandSector,
    ContentLanguage,
    ProgramGenre,
    ProgramTheme,
    PromoCategory,
    PromoType,
    Descriptor,
    Advertiser,
    AdvertiserGroup,
    ProductionHouse,
    Title,
    Promo,
    Program,
    Commercial,
    Channel,
    ChannelGenre,
    ChannelNetwork,
    Region,
    auto_title_code,
    auto_brandname_code,
    auto_descriptor_code
)
from video.models import Video
import shutil
try:
  from lxml import etree as ET
  # print("running with lxml.etree")
except ImportError:
  try:
    # Python 2.5
    import xml.etree.ElementTree as ET
    # print("running with cElementTree on Python 2.5+")
  except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as ET
        # print("running with cElementTree")
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as ET
          # print("running with ElementTree")
        except ImportError:
          print("Failed to import ElementTree from any known place")
from masters.similars import similar_maps as match_vendors
s3_client = boto3.client('s3')

app = Celery('masters')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')


def get_pending():
    c = VendorPromo.objects.filter(is_mapped=False).count() + VendorProgram.objects.filter(
            is_mapped=False).count() + VendorCommercial.objects.filter(is_mapped=False).count() + \
        VendorPromoCategory.objects.filter(is_mapped=False).count() + \
        VendorProgramGenre.objects.filter(is_mapped=False).count() + \
        VendorContentLanguage.objects.filter(is_mapped=False).count() + \
        VendorChannel.objects.filter(is_mapped=False).count()

    return c


@app.task
def all_compare(id):
    vmd = VendorMasterComparison.objects.get(id=id)
    compare_commercial(id)
    compare_program(id)
    compare_promo(id)
    vmd.status = "success"
    vmd.eta = 1
    vmd.save()


@app.task
def compare_commercial(id):
    vmd = VendorMasterComparison.objects.get(id=id)

    v = VendorCommercial.objects.all().values("title","descriptor").order_by("title","descriptor").annotate(Count('id')).filter(id__count__gt=1)
    steps = 3*math.ceil(v.count()/500)
    for i in range(int(math.ceil(v.count()/500))):
        query = reduce(
            operator.or_,
            (Q(title=t['title'], descriptor=t['descriptor']) for t in v[i*500:(i+1)*500])
        )
        n = VendorCommercial.objects.filter(query).update(is_mapped=True)
        vmd.eta += 1/steps
        vmd.save()


@app.task
def compare_program(id):
    vmd = VendorMasterComparison.objects.get(id=id)

    v = VendorProgram.objects.filter(channel__isnull=False).values("title","channel").order_by("title","channel").annotate(Count('id')).filter(id__count__gt=1)
    steps = 3*math.ceil(v.count()/500)

    for i in range(int(math.ceil(v.count()/500))):
        query = reduce(
            operator.or_,
            (Q(title=t['title'], channel__id=t['channel']) for t in v[i*500:(i+1)*500])
        )
        n = VendorProgram.objects.filter(query).update(is_mapped=True)
        vmd.eta += 1/steps
        vmd.save()


@app.task
def compare_promo(id):
    vmd = VendorMasterComparison.objects.get(id=id)

    v = VendorPromo.objects.all().values("title").order_by("title").annotate(Count('id')).filter(id__count__gt=1)
    steps = 3*math.ceil(v.count()/500)

    for i in range(int(math.ceil(v.count()/500))):
        query = reduce(
            operator.or_,
            (Q(title=t['title']) for t in v[i*500:(i+1)*500])
        )
        n = VendorPromo.objects.filter(query).update(is_mapped=True)
        vmd.eta += 1/steps
        vmd.save()


@app.task
def initial_master(date):
    c = Channel.objects.all()
    master_reports = []
    tt_data = "{}-{}-19".format(date.split("-")[-1], date.split("-")[-2])
    dt = datetime.datetime.strptime(date,"%Y-%m-%d")
    generate_masters.delay(dt.strftime("%Y%m%d"))


@app.task
def similar_commercials():
    qs = VendorCommercial.objects.all().filter(is_mapped=False)
    for instance in qs:
        vc = VendorCommercial.objects.exclude(id=instance.id, is_mapped=False) \
            .filter(brand_sector=instance.brand_sector, brand_category=instance.brand_category,
                    advertiser=instance.advertiser).filter(descriptor__trigram_similar=instance.descriptor,
                                                           title__trigram_similar=instance.title).first()
        if vc:
            instance.similars.add(vc)
            instance.save()


@app.task
def similar_commercial(id):
    obj = VendorCommercial.objects.get(id=id)
    qs = VendorCommercial.objects.filter(is_mapped=False, similars=obj).distinct()
    for instance in qs:
        vc = VendorCommercial.objects.exclude(id=instance.id, is_mapped=False) \
            .filter(brand_sector=instance.brand_sector, brand_category=instance.brand_category,
                    advertiser=instance.advertiser).filter(descriptor__trigram_similar=instance.descriptor,
                                                           title__trigram_similar=instance.title).first()
        if vc:
            instance.similars.add(vc)
            instance.similars.remove(obj)
            instance.save()
        else:
            instance.similars.remove(obj)
            instance.save()


@app.task
def similar_promos():
    qs = VendorPromo.objects.all().filter(is_mapped=False)
    for instance in qs:
        vc = VendorPromo.objects.exclude(id=instance.id, is_mapped=False) \
            .filter(brand_sector=instance.brand_sector, brand_category=instance.brand_category,
                    advertiser=instance.advertiser).filter(title__trigram_similar=instance.title).first()
        if vc:
            instance.similars.add(vc)
            instance.save()


@app.task
def similar_promo(id):
    obj = VendorPromo.objects.get(id=id)
    qs = VendorPromo.objects.all().filter(is_mapped=False,similars=obj).distinct()
    for instance in qs:
        vc = VendorPromo.objects.exclude(id=instance.id, is_mapped=False) \
            .filter(brand_sector=instance.brand_sector, brand_category=instance.brand_category,
                    advertiser=instance.advertiser).filter(title__trigram_similar=instance.title).first()
        if vc:
            instance.similars.add(vc)
            instance.similars.remove(obj)
            instance.save()
        else:
            instance.similars.remove(obj)
            instance.save()


@app.task
def load_brand(date, v):
    dobj = datetime.datetime.strptime(date, '%Y%m%d')
    ndobj = dobj + datetime.timedelta(days=1)
    ndate = ndobj.strftime('%Y%m%d')
    load_base(
        "https://barc-playout-files.s3.ap-south-1.amazonaws.com/Daily_Tam_Tabsons_Files/{}/{}/masters/BrandMstXml_{}.xml".format(
            v, date, ndate), date, v)


@app.task
def load_promo(date, v):
    dobj = datetime.datetime.strptime(date, '%Y%m%d')
    ndobj = dobj + datetime.timedelta(days=1)
    ndate = ndobj.strftime('%Y%m%d')
    load_promomaster(
        "https://barc-playout-files.s3.ap-south-1.amazonaws.com/Daily_Tam_Tabsons_Files/{}/{}/masters/PromoMstXml_{}.xml".format(
            v, date, ndate), date, v)


@app.task
def load_prg(date, v):
    dobj = datetime.datetime.strptime(date, '%Y%m%d')
    ndobj = dobj + datetime.timedelta(days=1)
    ndate = ndobj.strftime('%Y%m%d')
    load_prgmaster(
        "https://barc-playout-files.s3.ap-south-1.amazonaws.com/Daily_Tam_Tabsons_Files/{}/{}/masters/PrgMstXml_{}.xml".format(
            v, date, ndate), date, v)


@app.task
def load_masters(date, vendors, id=None, steps=2):
    for v in vendors.split(','):
        f_tasks = [load_brand.s(date, v), load_promo.s(date, v), load_prg.s(date, v)]
        chord(f_tasks)(loadReports.s(v, date, id, steps)).get()

@app.task
def load_vendor_masters(id, date):
    vmc = VendorMasterComparison.objects.get(id=id)
    send_mail("SuperMaster Processing Status - Started for TAM, PFT",
              "Hi Users, The Master processing for PFT, TAM is initiated", "support@tessact.com",
              ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
               "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])
    vendors = ["TAM","PFT"]
    for v in vendors:
        load_masters.delay(date,v, id, vendors.__len__())
    vmc.step=2
    vmc.status="wait"
    vmc.save()


@app.task
def load_durs(date, vendors):
    # dobj = datetime.datetime.strptime(date, '%Y%m%d')
    # ndobj = dobj + datetime.timedelta(days=1)
    for v in vendors.split(','):
        url = "https://barc-playout-files.s3.ap-south-1.amazonaws.com/Daily_Tam_Tabsons_Files/{}/{}/reports.zip".format(
            v, date)
        urllib.request.urlretrieve(url, '/tmp/reports.zip')
        sp.call('cd /tmp', shell=True)
        sp.call('sudo unzip reports.zip', shell=True)
        sp.call('sudo rm reports/*.xml', shell=True)
        sp.call('sudo mv *.xml reports/', shell=True)
        for f in glob.glob(os.path.join('/tmp/reports', '*.xml')):
            load_vendorreport.delay(f, v.upper())


@app.task
def accept_commercial(ids):
    qs = VendorCommercial.objects.all().filter(id__in=ids.split(","))
    qs.update(is_mapped=True)
    for vc in qs:
        brand_sector = BrandSector.objects.filter(name=vc.brand_sector).first()
        if not brand_sector:
            brand_sector = BrandSector.objects.create(name=vc.brand_sector)

        brand_category = BrandCategory.objects.filter(name=vc.brand_category, brand_sector=brand_sector).first()
        if not brand_category:
            brand_category = BrandCategory.objects.create(name=vc.brand_category, brand_sector=brand_sector)

        brand_name = BrandName.objects.filter(name=vc.brand_name, brand_category=brand_category).first()
        if not brand_name:
            brand_name = BrandName.objects.create(name=vc.brand_name, brand_category=brand_category)

        # title = Title.objects.filter(name=vc.title).first()
        # if not title:
        #     title = Title.objects.create(name=vc.title)

        advertiser_group = AdvertiserGroup.objects.filter(name=vc.advertiser_group).first()
        if not advertiser_group:
            advertiser_group = AdvertiserGroup.objects.create(name=vc.advertiser_group)

        advertiser  = Advertiser.objects.filter(name=vc.advertiser, advertiser_group=advertiser_group).first()
        if not advertiser:
            advertiser = Advertiser.objects.create(name=vc.advertiser, advertiser_group=advertiser_group)

        descriptor = Descriptor.objects.filter(text=vc.descriptor).first()
        if not descriptor:
            descriptor = Descriptor.objects.create(text=vc.descriptor)

        super_commercial, c = Commercial.objects.get_or_create(title=None, brand_name=brand_name,
                                                               advertiser=advertiser,
                                                               descriptor=descriptor)
        vc.commercial=super_commercial
        vc.is_mapped=True
        vc.save()
    for q in qs:
        similar_commercial.delay(q.id)


@app.task
def accept_promo(ids):
    qs = VendorPromo.objects.all().filter(id__in=ids.split(","))
    qs.update(is_mapped=True)
    for vc in qs:
        brand_sector = BrandSector.objects.filter(name=vc.brand_sector).first()
        if not brand_sector:
            brand_sector = BrandSector.objects.create(name=vc.brand_sector)

        brand_category = BrandCategory.objects.filter(name=vc.brand_category, brand_sector=brand_sector).first()
        if not brand_category:
            brand_category = BrandCategory.objects.create(name=vc.brand_category, brand_sector=brand_sector)

        brand_name = BrandName.objects.filter(name=vc.brand_name, brand_category=brand_category).first()
        if not brand_name:
            brand_name = BrandName.objects.create(name=vc.brand_name, brand_category=brand_category)

        # title = Title.objects.filter(name=vc.title).first()
        # if not title:
        #     title = Title.objects.create(name=vc.title)

        advertiser_group = AdvertiserGroup.objects.filter(name=vc.advertiser_group).first()
        if not advertiser_group and vc.advertiser_group:
            advertiser_group = AdvertiserGroup.objects.create(name=vc.advertiser_group)

        advertiser = Advertiser.objects.filter(name=vc.advertiser, advertiser_group=advertiser_group).first()
        if not advertiser:
            advertiser = Advertiser.objects.create(name=vc.advertiser, advertiser_group=advertiser_group)

        if vc.descriptor:
            descriptor = Descriptor.objects.filter(text=vc.descriptor).first()
            if not descriptor:
                descriptor = Descriptor.objects.create(text=vc.descriptor)
            super_promo, c = Promo.objects.get_or_create(title=None, brand_name=brand_name,
                                                         advertiser=advertiser,
                                                         descriptor=descriptor)
        else:
            descriptor = None
            super_promo, c = Promo.objects.get_or_create(title=None, brand_name=brand_name,
                                                         advertiser=advertiser)
        vc.promo=super_promo
        vc.is_mapped=True
        vc.save()
    for q in qs:
        similar_promo.delay(q.id)


@app.task
def accept_program(ids):
    qs = VendorProgram.objects.all().filter(id__in=ids.split(","))
    # qs.update(is_mapped=True)
    for vc in qs:
        title = Title.objects.filter(name=vc.title).first()
        if not title:
            title = Title.objects.create(name=vc.title)

        program_theme = ProgramTheme.objects.filter(name=vc.program_theme).first()
        if not program_theme:
            program_theme = ProgramTheme.objects.create(name=vc.program_theme)

        program_genre = ProgramGenre.objects.filter(name=vc.program_genre, program_theme=program_theme).first()
        if not program_genre:
            program_genre = ProgramGenre.objects.create(name=vc.program_genre, program_theme=program_theme)

        language = ContentLanguage.objects.filter(name=vc.language).first()
        if not language:
            language = ContentLanguage.objects.create(name=vc.language)

        if vc.prod_house and vc.channel:
            prod_house = ProductionHouse.objects.filter(name=vc.prod_house).first()
            if not prod_house:
                prod_house = ProductionHouse.objects.create(name=vc.prod_house)

            super_program, c = Program.objects.get_or_create(title=title, program_genre=program_genre,
                                                             language=language, prod_house=prod_house,
                                                             channel=vc.channel)
        elif vc.channel:
            super_program, c = Program.objects.get_or_create(title=title, program_genre=program_genre,
                                                             language=language, channel=vc.channel)
        else:
            super_program = None
        vc.program=super_program
        vc.is_mapped=True
        vc.save()


@app.task
def accept_program_genre(ids):
    qs = VendorProgramGenre.objects.all().filter(id__in=ids.split(","))
    for vc in qs:
        program_theme = ProgramTheme.objects.filter(name=vc.program_theme).first()
        if not program_theme:
            program_theme = ProgramTheme.objects.create(name=vc.program_theme)
        program_genre, c = ProgramGenre.objects.get_or_create(name=vc.name, program_theme=program_theme)
        vc.program_genre=program_genre
        vc.is_mapped=True
        vc.save()


@app.task
def accept_promo_category(ids):
    qs = VendorPromoCategory.objects.all().filter(id__in=ids.split(","))
    for vc in qs:
        super_promo_cat, c = PromoCategory.objects.get_or_create(name=vc.name)
        vc.promo_type=super_promo_cat
        vc.is_mapped=True
        vc.save()


@app.task
def accept_channel(ids):
    qs = VendorChannel.objects.all().filter(id__in=ids.split(","))
    for vc in qs:
        network = ChannelNetwork.objects.filter(name=vc.network_name if vc.network_name else '').first()
        if not network:
            network = ChannelNetwork.objects.create(name=vc.network_name if vc.network_name else '')

        region = Region.objects.filter(name=vc.region if vc.region else '').first()
        if not region:
            region = Region.objects.create(name=vc.region if vc.region else '')

        genre = ChannelGenre.objects.filter(name=vc.genre).first()
        if not genre:
            genre = ChannelGenre.objects.create(name=vc.genre)

        language = ContentLanguage.objects.filter(name=vc.language).first()
        if not language:
            language = ContentLanguage.objects.create(name=vc.language)

        channel = Channel.objects.filter(code=int(vc.code)).first()
        if not channel:
            channel = Channel.objects.create(name=vc.name, code=int(vc.code),genre=genre,region=region, network=network,
                                             language=language)
        else:
            channel.name = vc.name
            channel.genre=genre
            channel.region=region
            channel.network=network
            channel.language=language
            channel.save()
        vc.channel = channel
        vc.is_mapped=True
        vc.save()


@app.task
def accept_content_language(ids):
    qs = VendorContentLanguage.objects.all().filter(id__in=ids.split(","))
    for vc in qs:
        content_lang, c = ContentLanguage.objects.get_or_create(name=vc.name)
        vc.content_language = content_lang
        vc.is_mapped=True
        vc.save()


def clean_up():
    t = Title.objects.all().values("code").annotate(Count("id")).filter(id__count__gt=1)
    for tr in t:
        ts = Title.objects.all().filter(code=tr['code'])
        fid = Title.objects.all().filter(code=tr['code']).first().id
        tsr = Title.objects.all().filter(code=tr['code']).exclude(id=fid)
        for tss in tsr:
            tss.code = auto_title_code()
            tss.save()

    t = BrandName.objects.all().values("code").annotate(Count("id")).filter(id__count__gt=1)
    for tr in t:
        ts = BrandName.objects.all().filter(code=tr['code'])
        fid = BrandName.objects.all().filter(code=tr['code']).first().id
        tsr = BrandName.objects.all().filter(code=tr['code']).exclude(id=fid)
        for tss in tsr:
            tss.code = auto_brandname_code()
            tss.save()

    t = Descriptor.objects.all().values("code").annotate(Count("id")).filter(id__count__gt=1)
    for tr in t:
        ts = Descriptor.objects.all().filter(code=tr['code'])
        fid = Descriptor.objects.all().filter(code=tr['code']).first().id
        tsr = Descriptor.objects.all().filter(code=tr['code']).exclude(id=fid)
        for tss in tsr:
            tss.code = auto_descriptor_code()
            tss.save()

    # b = BrandName.objects.all().values("name").annotate(Count("id")).filter(id__count__gt=1)
    # for br in b:
    #     ts = BrandName.objects.all().filter(name=tr['name'])
    #     fid = BrandName.objects.all().filter(name=tr['name']).first().id
    #     tsr = BrandName.objects.all().filter(name=tr['name']).exclude(id=fid).values_list(id)
    #     for tss in tsr:
    #         c = Commercial.objects.filter(brand_name=tss)


@app.task
def downloadDirectoryFroms3(bucketName,remoteDirectoryName):
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(bucketName)
    ven = remoteDirectoryName.split("/")[1].upper()
    dt = remoteDirectoryName.split("/")[2]
    for object in bucket.objects.filter(Prefix = remoteDirectoryName):
        path = os.path.join("/tmp", object.key)
        if "masters" not in object.key and "xml" in object.key:
            print(object.key)
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            s3_resource.meta.client.download_file(bucketName, object.key, path)
            load_vendorreport.delay(path, ven)


@app.task
def loadReports(arg, ven, date, id, steps):
    vp = VendorProgram.objects.all().filter(is_mapped=False, channel__isnull=True)
    vp.delete()
    match_vendors()
    downloadDirectoryFroms3("barc-playout-files","Daily_Tam_Tabsons_Files/{}/{}".format(ven,date))
    match_videos(ven, date)
    if id:
        vmc = VendorMasterComparison.objects.get(id=id)
        vmc.eta += (1.0/steps)
        vmc.status = "process"
        if vmc.eta*steps == 1:
            vmc.step=3
            vmc.eta=0
            vmc.status="wait"
            c = get_pending()
            send_mail("SuperMaster Processing Status - Completed for {}".format(ven),
                      "Hi Users, The Master processing for {} is completed. We have a total of {} unique tags at the moment".format(
                          ven,
                          c),
                      "support@tessact.com",
                      ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
                       "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])
        vmc.save()
    else:
        c = get_pending()
        send_mail("SuperMaster Processing Status - Completed for {}".format(ven),
                  "Hi Users, The Master processing for {} is completed. We have a total of {} unique tags at the moment".format(
                      ven,
                      c),
                  "support@tessact.com",
                  ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
                   "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])


@app.task
def repurposeVendorReport(bucketName,remoteDirectoryName):
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(bucketName)
    ven = remoteDirectoryName.split("/")[1].upper()
    dt = remoteDirectoryName.split("/")[2]
    ndate = datetime.datetime.strptime(dt, '%Y%m%d').strftime("%Y-%m-%d")
    cloud_path = "/supermaster/{}/".format(dt)
    ven_tasks = []
    for object in bucket.objects.filter(Prefix = remoteDirectoryName):
        path = os.path.join("/tmp", object.key)
        output_path = os.path.join("/tmp/reports", os.path.basename(path))
        cloud_path = "supermaster/{}-{}-{}/{}".format(dt[0:4],dt[4:6], dt[6:8],os.path.basename(path))
        if "masters" not in object.key and "xml" in object.key:
            print(object.key)
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            s3_resource.meta.client.download_file(bucketName, object.key, path)
            ven_tasks.append(repurpose.s(path, output_path, cloud_path,None,ndate))
    return ven_tasks


def repurposeVendorCustomReport(bucketName,remoteDirectoryName, headers):
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(bucketName)
    ven = remoteDirectoryName.split("/")[1].upper()
    dt = remoteDirectoryName.split("/")[2]
    ndate = datetime.datetime.strptime(dt, '%Y%m%d').strftime("%Y-%m-%d")
    cloud_path = "/supermaster/{}/".format(dt)
    ven_tasks = []
    for object in bucket.objects.filter(Prefix = remoteDirectoryName):
        path = os.path.join("/tmp", object.key)
        output_path = os.path.join("/tmp/customreports", os.path.basename(path))
        cloud_path = "customreport/{}-{}-{}/{}".format(dt[0:4],dt[4:6], dt[6:8],os.path.basename(path))
        if "masters" not in object.key and "xml" in object.key:
            print(object.key)
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            s3_resource.meta.client.download_file(bucketName, object.key, path)
            ven_tasks.append(repurpose.s(path, output_path, cloud_path, headers,ndate))
    return ven_tasks


@app.task
def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


@app.task
def repurpose(file_path, output_path, cloud_path, headers=None, date=None):
    """
    repurpose("/tmp/Daily_Tam_Tabsons_Files/TAM/20190913/ANB_News_13-09-19.xml","/tmp/reports/ANB_News_13-09-19.xml", "supermaster/20190913/ANB_News_13-09-19.xml", None,"2019-09-13")
    repurpose("/tmp/Daily_Tam_Tabsons_Files/TAM/20190913/Comedy_Central_13-09-19.xml","/tmp/reports/Comedy_Central_13-09-19.xml", "supermaster/20190913/CC_13-09-19.xml", None,"2019-09-13")
    :param file_path:
    :param output_path:
    :return:
    """
    ven = file_path.split("/")[3]
    channel_name = " ".join(os.path.basename(file_path).split("_")[0:-1])
    start_time = datetime.datetime.now()
    header_row = ["Broadcastercode", "ContentType", "ContentTypeCode", "ChannelNameCode", "ChannelGenreCode", #5
                  "ChannelRegionCode", "ChannelLanguageCode", "Title", "TitleCode", "ContentLanguageCode", #10
                  "TelecastDate", "TelecastDay", "TelecastStartTime", "TelecastEndTime", "TelecastDuration", #15
                  "DescriptorCode", "BreakNumber", "PositionInBreak", "CountInBreak", "DurationInBreak", #20
                  "BreakDuration", "CountPerProgram", "DurationPerProgram", "TotalBreakCountPerProgram", #24
                  "TotalBreakDurationPerProgram", "PromoTypeCode", "PromoCategoryCode", "PromoChannelCode", #28
                  "PromoSponsorName", "PromoProgramNameCode", "PromoProgramThemeCode", "PromoProgramGenreCode", #32
                  "ProgramThemeCode", "ProgramGenreCode", "ProgramSegmentNumber", "NumberOfSegmentsInProgram", #36
                  "BrandSectorCode", "BrandCategoryCode", "ProductServiceNameCode", "BrandNameCode", #40
                  "SubBrandNameCode", #41
                  "AdvertiserCode", "AdvertisingGroupCode", "CommercialProgramNameCode", #44
                  "CommercialProgramThemeCode", "CommercialProgramGenreCode", "Sport", "OriginalOrRepeat", #48
                  "Live", "CombinedPositionInBreak", "CombinedCountInBreak", "PromoProgramStartTime", #52
                  "CommercialProgramStartTime", "SpotId", "LastModifiedDate", "AdBreakCode", #56
                  "PromoBroadcasterCode", "Beam", "Split", "Market", "SplitRegion", "SplitPlatform", #62
                  "ProdHouse"] #63
    if headers:
        allowed_rows = headers
    else:
        allowed_rows = header_row
    cdata_row = ["Title",
                 "PromoSponsorName", "AdBreakCode", "Beam", "Split", "Market", "SplitRegion", "SplitPlatform",
                 "ProdHouse"]
    tmp_tmp = file_path + ".tmp"
    sp.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, file_path])
    sp.run(["mv", tmp_tmp, file_path])
    tree = ElementTree.parse(file_path)
    root = tree.getroot()
    data = []
    for child in root:
        row_data = []
        for gc in child:
                row_data.append(gc.text)
        data.append(row_data)
        child.clear()
    root.clear()

    # start the tree creation
    top = ET.Element("BarcPlayoutMonitoring")
    tree = ET.ElementTree(top)

    # querying and caching the queryset for the long processing ahead
    pgs = Program.objects.all().select_related("program_genre", "program_genre__program_theme", "language", "title")
    cgs = Commercial.objects.all().select_related("brand_name", "descriptor")
    prgs = Promo.objects.all().select_related("brand_name")
    vpgs = VendorProgram.objects.all()
    vcgs = VendorCommercial.objects.all()
    vprgs = VendorPromo.objects.all()

    # language code remapping
    cls = ContentLanguage.objects.all().values('code', "name")
    vls_code = {}
    for cl in cls:
        v_code = VendorContentLanguage.objects.filter(name=cl['name']).first()
        if v_code:
            v_code=v_code.code
        vls_code[v_code]=cl['code']
    missing = [0,0,0]
    # start the remapping in the xml files
    for row_ind, row_data in enumerate(data):
        if row_data[1]=="Program":
            # program remapping

            # filter all master programs by the title name and channel code

            # filter vendor master entries for the original code
            vprg = vpgs.filter(title_code=str(row_data[8]),channel__code=row_data[3]).first()
            p = None
            if vprg:
                p = vprg.program
            else:
                p = pgs.filter(title__code=str(row_data[8]),channel__code=row_data[3]).first()

            reseed = ["TitleCode", "ProgramThemeCode", "ProgramGenreCode", "ContentLanguageCode", "ChannelLanguageCode"]
            if not p:
                # if no program is present then escape without creating entry
                # in this case we should check for vendor list mappings
                print("Missing Row Program")
                print(row_data[0:16])
                missing[0] += 1
                continue

            # if our code gets here then it has a valid remapping for program entry
            item = ET.SubElement(top, 'Item')
            for ind, d in enumerate(row_data):
                if header_row[ind] in allowed_rows:
                    element_sub_item = ET.SubElement(item, header_row[ind])
                    if d:
                        element_sub_item.text = str(d)
                    else:
                        element_sub_item.text = ''
                    if header_row[ind] in cdata_row:
                        element_sub_item.text = ET.CDATA(element_sub_item.text)
                    elif header_row[ind] in reseed and p:
                        # element_sub_item.text = str(p.title.code)
                        if header_row[ind] == "TitleCode":
                            element_sub_item.text = str(p.title.code)
                        elif header_row[ind] == "ProgramThemeCode":
                            element_sub_item.text = str(p.program_genre.program_theme.code+20) if p.program_genre else ''
                        elif header_row[ind] == "ChannelLanguageCode":
                            element_sub_item.text = str(vls_code[str(d)]) if d in vls_code else str(d)
                        elif header_row[ind] == "ProgramGenreCode":
                            element_sub_item.text = str(p.program_genre.code+220) if p.program_genre else ''
                        elif header_row[ind] == "ContentLanguageCode":
                            element_sub_item.text = str(p.language.code)
                        elif header_row[ind] == "ChannelLanguageCode":
                            element_sub_item.text = element_sub_item.text = str(vls_code[str(d)])
        elif row_data[1]=="Commercial":
            p_prg_code = row_data[43]
            reseed = ["TitleCode", "DescriptorCode", "BrandNameCode", "BrandSectorCode", "BrandCategoryCode",
                      "AdvertiserCode",
                      "AdvertisingGroupCode", "CommercialProgramThemeCode", "CommercialProgramGenreCode",
                      "CommercialProgramNameCode", "ChannelLanguageCode"]
            if p_prg_code:
                if ven=="TAM":
                    vp = VendorProgram.objects.filter(title_code=str(p_prg_code), channel__code=row_data[3], program__isnull=False).first()
                    if not vp:
                        continue
                    prg = vp.program
                else:
                    vp = VendorProgram.objects.filter(title_code=str(p_prg_code), channel__code=row_data[3], program__isnull=False).first()
                    if not vp:
                        prg = pgs.filter(title__code=int(p_prg_code), channel__code=row_data[3]).first()
                    else:
                        prg = vp.program
                        if not prg:
                            prg = pgs.filter(title__code=int(p_prg_code), channel__code=int(row_data[3])).first()
            else:
                prg = None
            vct = vcgs.filter(brand_name_code=str(row_data[8]), descriptor_code=str(row_data[15])).first()
            p = None
            if vct and not p:
                p = cgs.filter(id=vct.commercial.id).values("brand_name__name","brand_name__code", "brand_name__name","brand_name__code",
                                                            "brand_name__brand_category__brand_sector__name",
                                                            "brand_name__brand_category__brand_sector__code", "brand_name__brand_category__name",
                                                            "brand_name__brand_category__code","advertiser__name","advertiser__code",
                                                            "advertiser__advertiser_group__name","advertiser__advertiser_group__code","descriptor__text",
                                                            "descriptor__code").first()
            else:
                p = cgs.filter(brand_name__code=int(row_data[8]), descriptor__code=int(row_data[15])).values("brand_name__name","brand_name__code", "brand_name__name","brand_name__code",
                                                            "brand_name__brand_category__brand_sector__name",
                                                            "brand_name__brand_category__brand_sector__code", "brand_name__brand_category__name",
                                                            "brand_name__brand_category__code","advertiser__name","advertiser__code",
                                                            "advertiser__advertiser_group__name","advertiser__advertiser_group__code","descriptor__text",
                                                            "descriptor__code").first()
            if not p:
                print("Missing Row Commercial")
                print(row_data[0:16])
                missing[1]+=1
                continue
            item = ET.SubElement(top, 'Item')
            for ind, d in enumerate(row_data):
                if header_row[ind] in allowed_rows:
                    element_sub_item = ET.SubElement(item, header_row[ind])
                    if d:
                        element_sub_item.text = str(d)
                    else:
                        element_sub_item.text = ''
                    if header_row[ind] in cdata_row:
                        element_sub_item.text = ET.CDATA(element_sub_item.text)
                    elif header_row[ind] in reseed and p:
                        if header_row[ind] == "TitleCode" or header_row[ind]=="BrandNameCode":
                            element_sub_item.text = str(p['brand_name__code'])
                        elif header_row[ind] == "ChannelLanguageCode":
                            element_sub_item.text = element_sub_item.text = str(vls_code[str(d)]) if d in vls_code else str(d)
                        elif header_row[ind] == "ContentLanguageCode":
                            element_sub_item.text = element_sub_item.text = str(vls_code[str(d)]) if d in vls_code else str(d)
                        elif header_row[ind] == "DescriptorCode":
                            element_sub_item.text = str(p['descriptor__code']) if p['descriptor__code'] else ''
                        elif header_row[ind] == "BrandSectorCode":
                            element_sub_item.text = str(p['brand_name__brand_category__brand_sector__code'])
                        elif header_row[ind] == "BrandCategoryCode":
                            element_sub_item.text = str(p["brand_name__brand_category__code"])
                        elif header_row[ind] == "AdvertiserCode":
                            element_sub_item.text = str(p["advertiser__code"])
                        elif header_row[ind] == "AdvertisingGroupCode":
                            element_sub_item.text = str(p["advertiser__advertiser_group__code"])
                        elif header_row[ind] == "CommercialProgramNameCode" and prg:
                            element_sub_item.text = str(prg.title.code)
                        elif header_row[ind] == "CommercialProgramThemeCode" and prg:
                            element_sub_item.text = str(prg.program_genre.program_theme.code+20)
                        elif header_row[ind] == "CommercialProgramGenreCode" and prg:
                            element_sub_item.text = str(prg.program_genre.code+220)

                    if header_row[ind] == "ChannelLanguageCode":
                        element_sub_item.text = str(vls_code[str(d)]) if d in vls_code else str(d)
                    elif header_row[ind] == "ContentLanguageCode":
                        element_sub_item.text = str(vls_code[str(d)]) if d in vls_code else str(d)

        elif row_data[1]=="Promo":
            t = row_data[7]
            p_prg_code = row_data[29]
            if p_prg_code:
                vp = VendorProgram.objects.filter(title_code=str(p_prg_code), channel__code=int(row_data[3])).first()
                if not vp:
                    prg = pgs.filter(title__code=int(p_prg_code), channel__code=int(row_data[3])).first()
                else:
                    prg = vp.program
                    if not prg:
                        prg = pgs.filter(title__code=int(p_prg_code), channel__code=int(row_data[3])).first()
            else:
                prg = None
            reseed = ["TitleCode", "DescriptorCode", "BrandNameCode", "BrandSectorCode", "BrandCategoryCode",
                      "AdvertiserCode",
                      "AdvertisingGroupCode", "PromoProgramNameCode", "PromoProgramGenreCode",
                      "PromoProgramThemeCode", "ChannelLanguageCode", "ContentLanguageCode", "PromoTypeCode",
                      "PromoCategoryCode"]
            vct = VendorPromo.objects.filter(brand_name_code=str(row_data[8])).first()
            p = None
            if vct and not p:
                p = prgs.filter(id=vct.promo.id).values("brand_name__name", "brand_name__code", "brand_name__name", "brand_name__code",
                                                        "brand_name__brand_category__brand_sector__name",
                                                        "brand_name__brand_category__brand_sector__code", "brand_name__brand_category__name",
                                                        "brand_name__brand_category__code", "advertiser__name", "advertiser__code",
                                                        "advertiser__advertiser_group__name", "advertiser__advertiser_group__code", "descriptor__text",
                                                        "descriptor__code").first()
            else:
                p = prgs.filter(brand_name__code=int(row_data[8])).values("brand_name__name", "brand_name__code", "brand_name__name",
                                                                          "brand_name__code",
                                                                          "brand_name__brand_category__brand_sector__name",
                                                                          "brand_name__brand_category__brand_sector__code",
                                                                          "brand_name__brand_category__name",
                                                                          "brand_name__brand_category__code", "advertiser__name",
                                                                          "advertiser__code",
                                                                          "advertiser__advertiser_group__name",
                                                                          "advertiser__advertiser_group__code", "descriptor__text",
                                                                          "descriptor__code").first()
            if not p:
                print("Missing Row Promo")
                print(row_data[0:16])
                missing[2] += 1
                continue
            item = ET.SubElement(top, 'Item')
            for ind, d in enumerate(row_data):
                if header_row[ind] in allowed_rows:
                    element_sub_item = ET.SubElement(item, header_row[ind])
                    if d:
                        element_sub_item.text = str(d)
                    else:
                        element_sub_item.text = ''
                    if header_row[ind] in cdata_row:
                        element_sub_item.text = ET.CDATA(element_sub_item.text)
                    elif header_row[ind] in reseed and p:
                        if header_row[ind] == "TitleCode" or header_row[ind]=="BrandNameCode":
                            element_sub_item.text = str(p['brand_name__code'])
                        elif header_row[ind] == "ChannelLanguageCode":
                            element_sub_item.text = str(vls_code[str(d)]) if d in vls_code else str(d)
                        elif header_row[ind] == "ContentLanguageCode":
                            element_sub_item.text = str(vls_code[str(d)]) if d in vls_code else str(d)
                        elif header_row[ind] == "DescriptorCode":
                            element_sub_item.text = str(p['descriptor__code']) if p['descriptor__code'] else ''
                        elif header_row[ind] == "BrandSectorCode":
                            element_sub_item.text = str(p['brand_name__brand_category__brand_sector__code'])
                        elif header_row[ind] == "BrandCategoryCode":
                            element_sub_item.text = '0'
                        elif header_row[ind] == "AdvertiserCode":
                            element_sub_item.text = str(p["advertiser__code"])
                        elif header_row[ind] == "AdvertisingGroupCode":
                            element_sub_item.text = str(p["advertiser__advertiser_group__code"]) if p["advertiser__advertiser_group__code"] else ''
                        elif header_row[ind] == "PromoProgramNameCode" and prg:
                            element_sub_item.text = str(prg.title.code)
                        elif header_row[ind] == "PromoProgramThemeCode" and prg:
                            element_sub_item.text = str(prg.program_genre.program_theme.code+20)
                        elif header_row[ind] == "PromoProgramGenreCode" and prg:
                            element_sub_item.text = str(prg.program_genre.code+220)
                        elif header_row[ind] == "PromoTypeCode" :
                            element_sub_item.text = str(p["brand_name__brand_category__code"])
                        elif header_row[ind] == "PromoCategoryCode":
                            element_sub_item.text = str(d)[-1]
                    if header_row[ind] == "ChannelLanguageCode":
                        element_sub_item.text = str(vls_code[str(d)]) if d in vls_code else str(d)
                    elif header_row[ind] == "ContentLanguageCode":
                        element_sub_item.text = str(vls_code[str(d)]) if d in vls_code else str(d)
        elif row_data[1]=="Feed Missing":
            p_prg_code = row_data[43]
            reseed = ["TitleCode", "DescriptorCode", "BrandNameCode", "BrandSectorCode", "BrandCategoryCode",
                      "AdvertiserCode",
                      "AdvertisingGroupCode", "CommercialProgramThemeCode", "CommercialProgramGenreCode",
                      "CommercialProgramNameCode", "ChannelLanguageCode"]
            if p_prg_code:
                if ven == "TAM":
                    vp = VendorProgram.objects.filter(title_code=str(p_prg_code), channel__code=row_data[3],
                                                      program__isnull=False).first()
                    if not vp:
                        continue
                    prg = vp.program
                else:
                    vp = VendorProgram.objects.filter(title_code=str(p_prg_code), channel__code=row_data[3],
                                                      program__isnull=False).first()
                    if not vp:
                        prg = pgs.filter(title__code=int(p_prg_code), channel__code=row_data[3]).first()
                    else:
                        prg = vp.program
                        if not prg:
                            prg = pgs.filter(title__code=int(p_prg_code), channel__code=int(row_data[3])).first()
            else:
                prg = None
            vct = vcgs.filter(brand_name_code=str(row_data[8]), descriptor_code=str(row_data[15])).first()
            p = None
            if vct and not p:
                p = cgs.filter(id=vct.commercial.id).values("brand_name__name", "brand_name__code", "brand_name__name",
                                                            "brand_name__code",
                                                            "brand_name__brand_category__brand_sector__name",
                                                            "brand_name__brand_category__brand_sector__code",
                                                            "brand_name__brand_category__name",
                                                            "brand_name__brand_category__code", "advertiser__name",
                                                            "advertiser__code",
                                                            "advertiser__advertiser_group__name",
                                                            "advertiser__advertiser_group__code", "descriptor__text",
                                                            "descriptor__code").first()
            else:
                p = cgs.filter(brand_name__code=int(row_data[8]), descriptor__code=int(row_data[15])).values(
                    "brand_name__name", "brand_name__code", "brand_name__name", "brand_name__code",
                    "brand_name__brand_category__brand_sector__name",
                    "brand_name__brand_category__brand_sector__code", "brand_name__brand_category__name",
                    "brand_name__brand_category__code", "advertiser__name", "advertiser__code",
                    "advertiser__advertiser_group__name", "advertiser__advertiser_group__code", "descriptor__text",
                    "descriptor__code").first()
            if not p:
                print(row_data[0:16])
                missing[1] += 1
                continue
            item = ET.SubElement(top, 'Item')
            for ind, d in enumerate(row_data):
                if header_row[ind] in allowed_rows:
                    element_sub_item = ET.SubElement(item, header_row[ind])
                    if d:
                        element_sub_item.text = str(d)
                    else:
                        element_sub_item.text = ''
                    if header_row[ind] in cdata_row:
                        element_sub_item.text = ET.CDATA(element_sub_item.text)
                    elif header_row[ind] in reseed and p:
                        if header_row[ind] == "TitleCode" or header_row[ind] == "BrandNameCode":
                            element_sub_item.text = str(p['brand_name__code'])
                        elif header_row[ind] == "ChannelLanguageCode":
                            element_sub_item.text = element_sub_item.text = str(
                                vls_code[str(d)]) if d in vls_code else str(d)
                        elif header_row[ind] == "ContentLanguageCode":
                            element_sub_item.text = element_sub_item.text = str(
                                vls_code[str(d)]) if d in vls_code else str(d)
                        elif header_row[ind] == "DescriptorCode":
                            element_sub_item.text = str(p['descriptor__code']) if p['descriptor__code'] else ''
                        elif header_row[ind] == "BrandSectorCode":
                            element_sub_item.text = str(p['brand_name__brand_category__brand_sector__code'])
                        elif header_row[ind] == "BrandCategoryCode":
                            element_sub_item.text = str(p["brand_name__brand_category__code"])
                        elif header_row[ind] == "AdvertiserCode":
                            element_sub_item.text = str(p["advertiser__code"])
                        elif header_row[ind] == "AdvertisingGroupCode":
                            element_sub_item.text = str(p["advertiser__advertiser_group__code"])
                        elif header_row[ind] == "CommercialProgramNameCode" and prg:
                            element_sub_item.text = str(prg.title.code)
                        elif header_row[ind] == "CommercialProgramThemeCode" and prg:
                            element_sub_item.text = str(prg.program_genre.program_theme.code + 20)
                        elif header_row[ind] == "CommercialProgramGenreCode" and prg:
                            element_sub_item.text = str(prg.program_genre.code + 220)

                    if header_row[ind] == "ChannelLanguageCode":
                        element_sub_item.text = str(vls_code[str(d)]) if d in vls_code else str(d)
                    elif header_row[ind] == "ContentLanguageCode":
                        element_sub_item.text = str(vls_code[str(d)]) if d in vls_code else str(d)
    print(datetime.datetime.now() - start_time)
    print("Missing Count  for {}: {}".format(channel_name, missing))
    check_or_create_file(output_path)
    indent(top)
    with open(output_path, 'wb') as xml_file:
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    top.clear()
    upload_file(output_path, "barc-playout-files", cloud_path)
    if Channel.objects.filter(name__iexact=channel_name).first():
        ch = Channel.objects.filter(name__iexact=channel_name).first()
        MasterReport.objects.create(date=date, eta=1.0, channel=ch, file="https://barc-playout-files.s3.ap-south-1.amazonaws.com/"+cloud_path)


def tcr2sec(tcr):
    h = int(tcr.split(":")[0])
    m = int(tcr.split(":")[1])
    s = int(tcr.split(":")[2])
    return int(h*3600+m*60+s)


def date2date(d):
    dt = datetime.datetime.strptime(d,"%d/%m/%Y")
    return dt.strftime("%Y-%m-%d")


@app.task
def load_vendorreport(file='/tmp/Zee_TV_18-04-19.xml', vendor="TABSONS"):

    tree = ElementTree.parse(file)
    root = tree.getroot()
    ven, c = Vendor.objects.get_or_create(name=vendor.upper())
    vrcs = []
    vrps = []
    vrpgs = []
    for child in root:
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        child.clear()
        channel = Channel.objects.filter(code=int(row_data[3])).first()
        if not channel:
            break
        if row_data[1] == "Commercial":
            dur = tcr2sec(row_data[14])
            vc = VendorCommercial.objects.filter(title_code=row_data[8], descriptor_code=row_data[15], vendor=ven).first()
            vrc = VendorReportCommercial(date=date2date(row_data[10]), channel=channel, vendor=ven, commercial=vc,
                                         start_time=row_data[12], end_time=row_data[13], duration=dur)
            vrcs.append(vrc)
        if row_data[1] == "Program":
            dur = tcr2sec(row_data[14])
            vc = VendorProgram.objects.filter(title_code=row_data[8], channel=channel, vendor=ven).first()
            vrpg = VendorReportProgram(date=date2date(row_data[10]), channel=channel, vendor=ven, program=vc,
                                       start_time=row_data[12], end_time=row_data[13], duration=dur)
            vrpgs.append(vrpg)
        if row_data[1] == "Promo":
            dur = tcr2sec(row_data[14])
            vc = VendorPromo.objects.filter(title_code=row_data[8], vendor=ven).first()
            vrp = VendorReportPromo(date=date2date(row_data[10]), channel=channel, vendor=ven, promo=vc,
                                    start_time=row_data[12], end_time=row_data[13], duration=dur)
            vrps.append(vrp)
    root.clear()
    VendorReportCommercial.objects.bulk_create(vrcs, 2000)
    VendorReportPromo.objects.bulk_create(vrps, 2000)
    VendorReportProgram.objects.bulk_create(vrpgs, 2000)


@app.task
def zip_masters(t, date, id=None):
    dobj = datetime.datetime.strptime(date, '%Y%m%d')
    # ndobj = dobj + datetime.timedelta(days=1)
    ndate = dobj.strftime('%Y-%m-%d')
    shutil.make_archive("/tmp/BARC_MasterReportsXmls_{}".format(date),"zip","/tmp/masters")
    upload_file("/tmp/BARC_MasterReportsXmls_{}.zip".format(date), "barc-playout-files", "supermaster/{}/BARC_MasterReportsXmls_{}.zip".format(ndate, date))
    if id:
        vmc = VendorMasterComparison.objects.get(id=id)
        vmc.eta += (1.0/2)
        vmc.status = "process"
        vmc.save()
    SuperMaster.objects.create(date=ndate, file="https://barc-playout-files.s3.ap-south-1.amazonaws.com/supermaster/{}/BARC_MasterReportsXmls_{}.zip".format(ndate,date))
    all_report_tasks = generate_reports(date, id)
    all_report_tasks.get()
    return True


@app.task
def zip_reports(t, date, id):
    dobj = datetime.datetime.strptime(date, '%Y%m%d')
    ndate = dobj.strftime('%Y-%m-%d')
    shutil.make_archive("/tmp/BARC_ChannelReportsXmls_{}".format(date),"zip","/tmp/reports")
    upload_file("/tmp/BARC_ChannelReportsXmls_{}.zip".format(date), "barc-playout-files", "supermaster/{}/BARC_ChannelReportsXmls_{}.zip".format(ndate, date))
    upload_file("/tmp/BARC_ChannelReportsXmls_{}.zip".format(date), "barc-playout-files",
                "supermaster/{}/channelreports.zip".format(ndate))
    send_mail("SuperMaster Processing Status - Report Generation Completed for TAM, PFT",
              "Hi Users, The Master Report Generation for PFT is completed. please find the changelog at "
              "https://barc-playout-files.s3.ap-south-1.amazonaws.com/supermaster/{}/BARC_MasterReportsXmls_{}.zip and "
              "master reports at "
              "https://barc-playout-files.s3.ap-south-1.amazonaws.com/supermaster/{}/BARC_ChannelReportsXmls_{}.zip . "
              "You can download the files by clicking on the links".format(ndate, date, ndate, date),
              "support@tessact.com",
              ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
               "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in", "operations@barcindia.co.in"])
    if id:
        vmc = VendorMasterComparison.objects.get(id=id)
        vmc.eta = 1.0
        vmc.status = "finish"
        vmc.save()
    return True


@app.task
def zip_custom_reports(t, date, id=None):
    dobj = datetime.datetime.strptime(date, '%Y%m%d')
    ndate = dobj.strftime('%Y-%m-%d')
    shutil.make_archive("/tmp/archieves/BARC_ChannelReportsXmls_{}".format(date),"zip","/tmp/customreports")
    upload_file("/tmp/archieves/BARC_ChannelReportsXmls_{}.zip".format(date), "barc-playout-files", "custom/{}/BARC_ChannelReportsXmls_{}.zip".format(ndate, date))
    send_mail("SuperMaster Processing Status - Custom Report Generation Completed for TAM, PFT",
              "Hi Users, The Custom Report Generation is completed. please find the masters at "
              "https://barc-playout-files.s3.ap-south-1.amazonaws.com/supermaster/{}/BARC_MasterReportsXmls_{}.zip and "
              "custom reports at "
              "https://barc-playout-files.s3.ap-south-1.amazonaws.com/custom/{}/BARC_ChannelReportsXmls_{}.zip . "
              "You can download the files by clicking on the links".format(ndate, date, ndate, date),
              "support@tessact.com",
              ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
               "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in", "operations@barcindia.co.in"])
    if id:
        vmc = VendorMasterComparison.objects.get(id=id)
        vmc.eta = 1.0
        vmc.status = "finish"
        vmc.save()
    return True


@app.task
def generate_masters(date):
    id = VendorMasterComparison.objects.all().order_by("created_on").last().id
    if id:
        vmc = VendorMasterComparison.objects.get(id=id)
        vmc.step = 4
        vmc.status = "process"
        vmc.save()
    clean_up()
    shutil.rmtree('/tmp/masters')
    check_or_create_file('/tmp/masters/tmp.txt')
    dobj = datetime.datetime.strptime(date, '%Y%m%d')
    ndobj = dobj + datetime.timedelta(days=1)
    ndate = ndobj.strftime('%Y%m%d')
    subtasks = [
        generate_brandmaster.s("/tmp/masters/BrandMstXml_{}.xml".format(ndate)),
        generate_chnmaster.s("/tmp/masters/ChnMstXml_{}.xml".format(ndate)),
        generate_genremaster.s("/tmp/masters/Genremstxml_{}.xml".format(ndate)),
        generate_langmaster.s("/tmp/masters/ContentLanguagexml_{}.xml".format(ndate)),
        generate_prgmaster.s("/tmp/masters/PrgMstXml_{}.xml".format(ndate)),
        generate_promocatmaster.s("/tmp/masters/PromoCategoryXml_{}.xml".format(ndate)),
        generate_promomaster.s("/tmp/masters/PromoMstXml_{}.xml".format(ndate))
    ]

    c = chord(subtasks)(zip_masters.s(date, id))
    results = c()
    return True


@app.task
def generate_vendormasters(date):
    clean_up()
    dobj = datetime.datetime.strptime(date, '%Y%m%d')
    ndobj = dobj + datetime.timedelta(days=1)
    ndate = ndobj.strftime('%Y%m%d')
    generate_vendorbrandmaster.delay("/tmp/masters/BrandMstXml_{}.xml".format(ndate))
    generate_vendorchnmaster.delay("/tmp/masters/ChnMstXml_{}.xml".format(ndate))
    generate_vendorgenremaster.delay("/tmp/masters/Genremstxml_{}.xml".format(ndate))
    generate_vendorlangmaster.delay("/tmp/masters/ContentLanguagexml_{}.xml".format(ndate))
    generate_vendorprgmaster.delay("/tmp/masters/PrgMstXml_{}.xml".format(ndate))
    generate_vendorpromocatmaster.delay("/tmp/masters/PromoCategoryXml_{}.xml".format(ndate))
    generate_vendorpromomaster.delay("/tmp/masters/PromoMstXml_{}.xml".format(ndate))
    return True


@app.task
def generate_changelog(ven, date):
    clean_up()
    dobj = datetime.datetime.strptime(date, '%Y-%m-%d')
    ndobj = dobj + datetime.timedelta(days=1)
    ndate = ndobj.strftime('%Y%m%d')
    generate_brandmaster_changelog.delay("/tmp/masterchanges/BrandMstXml_{}.json".format(ndate), date, ven)
    generate_chnmaster_changelog.delay("/tmp/masterchanges/ChnMstXml_{}.json".format(ndate), date, ven)
    generate_genremaster_changelog.delay("/tmp/masterchanges/Genremstxml_{}.json".format(ndate), date, ven)
    generate_langmaster_changelog.delay("/tmp/masterchanges/ContentLanguagexml_{}.json".format(ndate), date, ven)
    generate_prgmaster_changelog.delay("/tmp/masterchanges/PrgMstXml_{}.json".format(ndate), date, ven)
    generate_promocatmaster_changelog.delay("/tmp/masterchanges/PromoCategoryXml_{}.json".format(ndate), date, ven)
    generate_promomaster_changelog.delay("/tmp/masterchanges/PromoMstXml_{}.json".format(ndate), date, ven)
    return True


@app.task
def generate_chnmaster_changelog(output_path, date, ven):
    items = []
    with open(output_path, 'w+') as json_file:
        json.dump(items, json_file)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp/",""))
    return True


@app.task
def generate_genremaster_changelog(output_path, date, ven):
    items = []
    with open(output_path, 'w+') as json_file:
        json.dump(items, json_file)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp/",""))
    return True


@app.task
def generate_langmaster_changelog(output_path, date, ven):
    items = []
    with open(output_path, 'w+') as json_file:
        json.dump(items, json_file)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp/",""))
    return True


@app.task
def generate_promocatmaster_changelog(output_path, date, ven):
    items = []
    with open(output_path, 'w+') as json_file:
        json.dump(items, json_file)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp/",""))
    return True


@app.task
def generate_brandmaster_changelog(output_path, date, ven):
    data = Commercial.objects.filter(modified_on__date__gte=date)
    items = []
    for row_data in tqdm.tqdm(data):
        tmp_data = {}
        vc = row_data.vendorcommercial_set.filter(vendor__name=ven).first()
        if vc and not row_data.deleted:
            tmp_data['original_id'] = str(vc.id)
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": ""
            }
            tmp_data['brand_name'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": "",
                "brand_category": {
                    "name": row_data.brand_name.brand_category.name,
                    "code": row_data.brand_name.brand_category.code,
                    "original_code": "",
                    "brand_sector": {
                        "name": row_data.brand_name.brand_category.brand_sector.name if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "code": row_data.brand_name.brand_category.brand_sector.code if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "original_code": ""
                    }
                }
            }
            tmp_data['advertiser'] = {
                "name": row_data.advertiser.name,
                "code": row_data.advertiser.code,
                "original_code": "",
                "advertiser_group": {
                    "name": row_data.advertiser.advertiser_group.name if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "code": row_data.advertiser.advertiser_group.code if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "original_code": "",
                }
            }
            tmp_data['descriptor'] = {
                "text": row_data.descriptor.text if row_data.descriptor else "",
                "code": row_data.descriptor.code if row_data.descriptor else "",
                "original_code": ""
            }
            tmp_data['video'] = ""
            tmp_data['status']="modified"
        if vc and row_data.deleted:
            tmp_data['original_id'] = str(vc.id)
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": ""
            }
            tmp_data['brand_name'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": "",
                "brand_category": {
                    "name": row_data.brand_name.brand_category.name,
                    "code": row_data.brand_name.brand_category.code,
                    "original_code": "",
                    "brand_sector": {
                        "name": row_data.brand_name.brand_category.brand_sector.name if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "code": row_data.brand_name.brand_category.brand_sector.code if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "original_code": ""
                    }
                }
            }
            tmp_data['advertiser'] = {
                "name": row_data.advertiser.name,
                "code": row_data.advertiser.code,
                "original_code": "",
                "advertiser_group": {
                    "name": row_data.advertiser.advertiser_group.name if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "code": row_data.advertiser.advertiser_group.code if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "original_code": "",
                }
            }
            tmp_data['descriptor'] = {
                "text": row_data.descriptor.text if row_data.descriptor else "",
                "code": row_data.descriptor.code if row_data.descriptor else "",
                "original_code": ""
            }
            tmp_data['video'] = ""
            tmp_data['status']="inactive"
        elif not row_data.deleted:
            tmp_data['original_id'] = ""
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": ""
            }
            tmp_data['brand_name'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": "",
                "brand_category": {
                    "name": row_data.brand_name.brand_category.name,
                    "code": row_data.brand_name.brand_category.code,
                    "original_code": "",
                    "brand_sector": {
                        "name": row_data.brand_name.brand_category.brand_sector.name if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "code": row_data.brand_name.brand_category.brand_sector.code if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "original_code": ""
                    }
                }
            }
            tmp_data['advertiser'] = {
                "name": row_data.advertiser.name,
                "code": row_data.advertiser.code,
                "original_code": "",
                "advertiser_group": {
                    "name": row_data.advertiser.advertiser_group.name if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "code": row_data.advertiser.advertiser_group.code if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "original_code": "",
                }
            }
            tmp_data['descriptor'] = {
                "text": row_data.descriptor.text if row_data.descriptor else "",
                "code": row_data.descriptor.code if row_data.descriptor else "",
                "original_code": ""
            }
            tmp_data['video'] = ""
            tmp_data['status'] = "new"
        elif row_data.deleted:
            tmp_data['original_id'] = ""
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": ""
            }
            tmp_data['brand_name'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": "",
                "brand_category": {
                    "name": row_data.brand_name.brand_category.name,
                    "code": row_data.brand_name.brand_category.code,
                    "original_code": "",
                    "brand_sector": {
                        "name": row_data.brand_name.brand_category.brand_sector.name if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "code": row_data.brand_name.brand_category.brand_sector.code if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "original_code": ""
                    }
                }
            }
            tmp_data['advertiser'] = {
                "name": row_data.advertiser.name,
                "code": row_data.advertiser.code,
                "original_code": "",
                "advertiser_group": {
                    "name": row_data.advertiser.advertiser_group.name if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "code": row_data.advertiser.advertiser_group.code if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "original_code": "",
                }
            }
            tmp_data['descriptor'] = {
                "text": row_data.descriptor.text if row_data.descriptor else "",
                "code": row_data.descriptor.code if row_data.descriptor else "",
                "original_code": ""
            }
            tmp_data['video'] = ""
            tmp_data['status'] = "inactive"
        items.append(tmp_data)
    with open(output_path, 'w+') as json_file:
        json.dump(items, json_file)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp/",""))
    return True

@app.task
def generate_promomaster_changelog(output_path, date, ven):
    data = Promo.objects.filter(modified_on__date__gte=date)
    items = []
    for row_data in tqdm.tqdm(data):
        tmp_data = {}
        vc = row_data.vendorpromo_set.filter(vendor__name=ven).first()
        if vc and not row_data.deleted:
            tmp_data['original_id'] = str(vc.id)
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": ""
            }
            tmp_data['brand_name'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": "",
                "brand_category": {
                    "name": row_data.brand_name.brand_category.name,
                    "code": row_data.brand_name.brand_category.code,
                    "original_code": "",
                    "brand_sector": {
                        "name": row_data.brand_name.brand_category.brand_sector.name if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "code": row_data.brand_name.brand_category.brand_sector.code if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "original_code": ""
                    }
                }
            }
            tmp_data['advertiser'] = {
                "name": row_data.advertiser.name,
                "code": row_data.advertiser.code,
                "original_code": "",
                "advertiser_group": {
                    "name": row_data.advertiser.advertiser_group.name if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "code": row_data.advertiser.advertiser_group.code if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "original_code": "",
                }
            }
            tmp_data['descriptor'] = {
                "text": row_data.descriptor.text if row_data.descriptor else "",
                "code": row_data.descriptor.code if row_data.descriptor else "",
                "original_code": ""
            }
            tmp_data['video'] = ""
            tmp_data['status']="modified"
        elif vc and row_data.deleted:
            tmp_data['original_id'] = str(vc.id)
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": ""
            }
            tmp_data['brand_name'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": "",
                "brand_category": {
                    "name": row_data.brand_name.brand_category.name,
                    "code": row_data.brand_name.brand_category.code,
                    "original_code": "",
                    "brand_sector": {
                        "name": row_data.brand_name.brand_category.brand_sector.name if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "code": row_data.brand_name.brand_category.brand_sector.code if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "original_code": ""
                    }
                }
            }
            tmp_data['advertiser'] = {
                "name": row_data.advertiser.name,
                "code": row_data.advertiser.code,
                "original_code": "",
                "advertiser_group": {
                    "name": row_data.advertiser.advertiser_group.name if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "code": row_data.advertiser.advertiser_group.code if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "original_code": "",
                }
            }
            tmp_data['descriptor'] = {
                "text": row_data.descriptor.text if row_data.descriptor else "",
                "code": row_data.descriptor.code if row_data.descriptor else "",
                "original_code": ""
            }
            tmp_data['video'] = ""
            tmp_data['status']="inactive"
        elif row_data.deleted:
            tmp_data['original_id'] = ""
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": ""
            }
            tmp_data['brand_name'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": "",
                "brand_category": {
                    "name": row_data.brand_name.brand_category.name,
                    "code": row_data.brand_name.brand_category.code,
                    "original_code": "",
                    "brand_sector": {
                        "name": row_data.brand_name.brand_category.brand_sector.name if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "code": row_data.brand_name.brand_category.brand_sector.code if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "original_code": ""
                    }
                }
            }
            tmp_data['advertiser'] = {
                "name": row_data.advertiser.name,
                "code": row_data.advertiser.code,
                "original_code": "",
                "advertiser_group": {
                    "name": row_data.advertiser.advertiser_group.name if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "code": row_data.advertiser.advertiser_group.code if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "original_code": "",
                }
            }
            tmp_data['descriptor'] = {
                "text": row_data.descriptor.text if row_data.descriptor else "",
                "code": row_data.descriptor.code if row_data.descriptor else "",
                "original_code": ""
            }
            tmp_data['video'] = ""
            tmp_data['status']="modified"
        else:
            tmp_data['original_id'] = ""
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": ""
            }
            tmp_data['brand_name'] = {
                "name": row_data.brand_name.name,
                "code": row_data.brand_name.code,
                "original_code": "",
                "brand_category": {
                    "name": row_data.brand_name.brand_category.name,
                    "code": row_data.brand_name.brand_category.code,
                    "original_code": "",
                    "brand_sector": {
                        "name": row_data.brand_name.brand_category.brand_sector.name if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "code": row_data.brand_name.brand_category.brand_sector.code if row_data.brand_name.brand_category and row_data.brand_name.brand_category.brand_sector else "",
                        "original_code": ""
                    }
                }
            }
            tmp_data['advertiser'] = {
                "name": row_data.advertiser.name,
                "code": row_data.advertiser.code,
                "original_code": "",
                "advertiser_group": {
                    "name": row_data.advertiser.advertiser_group.name if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "code": row_data.advertiser.advertiser_group.code if row_data.advertiser and row_data.advertiser.advertiser_group else "",
                    "original_code": "",
                }
            }
            tmp_data['descriptor'] = {
                "text": row_data.descriptor.text if row_data.descriptor else "",
                "code": row_data.descriptor.code if row_data.descriptor else "",
                "original_code": ""
            }
            tmp_data['video'] = ""
            tmp_data['status'] = "new"
        items.append(tmp_data)
    with open(output_path, 'w+') as json_file:
        json.dump(items, json_file)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp/",""))
    return True


@app.task
def generate_prgmaster_changelog(output_path, date, ven):
    data = Program.objects.filter(modified_on__date__gte=date)
    items = []
    for row_data in tqdm.tqdm(data):
        tmp_data = {}
        vc = row_data.vendorprogram_set.filter(vendor__name=ven).first()
        if vc and not row_data.deleted:
            tmp_data['original_id'] = str(vc.id)
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.title.name,
                "code": row_data.title.code,
                "original_code": ""
            }
            tmp_data['language'] = {
                "name": row_data.language.name,
                "code": row_data.language.code,
                "original_code": "",
            }
            tmp_data['prod_house'] = {
                "text": row_data.prod_house.name if row_data.prod_house else "",
                "code": row_data.prod_house.code if row_data.prod_house else "",
                "original_code": ""
            }
            tmp_data['program_genre'] = {
                "name": row_data.program_genre.name,
                "code": row_data.program_genre.code,
                "original_code": "",
                "program_theme": {
                    "name": row_data.program_genre.program_theme.name,
                    "code": row_data.program_genre.program_theme.code,
                    "original_code": "",
                }
            }
            tmp_data['channel'] = {
                "name": row_data.channel.name,
                "code": row_data.channel.code,
                "original_code": "",
            }
            tmp_data['status']="modified"
        elif vc and row_data.deleted:
            tmp_data['original_id'] = str(vc.id)
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.title.name,
                "code": row_data.title.code,
                "original_code": ""
            }
            tmp_data['language'] = {
                "name": row_data.language.name,
                "code": row_data.language.code,
                "original_code": "",
            }
            tmp_data['prod_house'] = {
                "text": row_data.prod_house.name if row_data.prod_house else "",
                "code": row_data.prod_house.code if row_data.prod_house else "",
                "original_code": ""
            }
            tmp_data['program_genre'] = {
                "name": row_data.program_genre.name,
                "code": row_data.program_genre.code,
                "original_code": "",
                "program_theme": {
                    "name": row_data.program_genre.program_theme.name,
                    "code": row_data.program_genre.program_theme.code,
                    "original_code": "",
                }
            }
            tmp_data['channel'] = {
                "name": row_data.channel.name,
                "code": row_data.channel.code,
                "original_code": "",
            }
            tmp_data['status']="inactive"
        elif row_data.deleted:
            tmp_data['original_id'] = ""
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.title.name,
                "code": row_data.title.code,
                "original_code": ""
            }
            tmp_data['language'] = {
                "name": row_data.language.name,
                "code": row_data.language.code,
                "original_code": "",
            }
            tmp_data['prod_house'] = {
                "text": row_data.prod_house.name if row_data.prod_house else "",
                "code": row_data.prod_house.code if row_data.prod_house else "",
                "original_code": ""
            }
            tmp_data['program_genre'] = {
                "name": row_data.program_genre.name,
                "code": row_data.program_genre.code,
                "original_code": "",
                "program_theme": {
                    "name": row_data.program_genre.program_theme.name,
                    "code": row_data.program_genre.program_theme.code,
                    "original_code": "",
                }
            }
            tmp_data['channel'] = {
                "name": row_data.channel.name,
                "code": row_data.channel.code,
                "original_code": "",
            }
            tmp_data['status']="inactive"
        else:
            tmp_data['original_id'] = ""
            tmp_data['id'] = str(row_data.id)
            tmp_data['title'] = {
                "name": row_data.title.name,
                "code": row_data.title.code,
                "original_code": ""
            }
            tmp_data['language'] = {
                "name": row_data.language.name,
                "code": row_data.language.code,
                "original_code": "",
            }
            tmp_data['prod_house'] = {
                "text": row_data.prod_house.name if row_data.prod_house else "",
                "code": row_data.prod_house.code if row_data.prod_house else "",
                "original_code": ""
            }
            tmp_data['program_genre'] = {
                "name": row_data.program_genre.name,
                "code": row_data.program_genre.code,
                "original_code": "",
                "program_theme": {
                    "name": row_data.program_genre.program_theme.name,
                    "code": row_data.program_genre.program_theme.code,
                    "original_code": "",
                }
            }
            tmp_data['channel'] = {
                "name": row_data.channel.name,
                "code": row_data.channel.code,
                "original_code": "",
            }
            tmp_data['status'] = "new"
        items.append(tmp_data)
    with open(output_path, 'w+') as json_file:
        json.dump(items, json_file)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp/",""))
    return True


def indent(elem, level=0):
    i = "\n" + level*"\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


@app.task
def generate_brandmaster(output_path):
    top_txt = "BarcBrandMaster"
    header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                  "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                  "Advertisinggroupcode",
                  "Descriptor", "Descriptorcode"]
    cdata_row = ["Brandname", "Title", "Brandsector",
                 "Brandcategory", "Advertiser", "Advertisinggroup",
                 "Descriptor"]
    data = Commercial.objects.filter(deleted=False).values_list("brand_name__name","brand_name__code", "brand_name__name","brand_name__code", "brand_name__brand_category__brand_sector__name","brand_name__brand_category__brand_sector__code", "brand_name__brand_category__name","brand_name__brand_category__code","advertiser__name","advertiser__code","advertiser__advertiser_group__name","advertiser__advertiser_group__code","descriptor__text","descriptor__code")
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in tqdm.tqdm(data):
        item = ET.SubElement(main_top, 'Item')
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)

    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp",""))
    return True


@app.task
def generate_promomaster(output_path):
    top_txt = "BarcPromoMaster"
    header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                  "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                  "Advertisinggroupcode",
                  "Descriptor", "Descriptorcode"]
    cdata_row = ["Brandname", "Title", "Brandsector",
                 "Brandcategory", "Advertiser", "Advertisinggroup",
                 "Descriptor"]
    data = Promo.objects.filter(deleted=False).values_list("brand_name__name", "brand_name__code", "brand_name__name",
                                                           "brand_name__code", "brand_name__brand_category__brand_sector__name",
                                                           "brand_name__brand_category__brand_sector__code",
                                                           "brand_name__brand_category__name", "brand_name__brand_category__code",
                                                           "advertiser__name", "advertiser__code",
                                                           "advertiser__advertiser_group__name",
                                                           "advertiser__advertiser_group__code", "descriptor__text",
                                                           "descriptor__code")

    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in tqdm.tqdm(data):
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task
def generate_prgmaster(output_path):
    top_txt = "BarcProgramMaster"
    header_row = ["Channelnamecode", "Channelname", "Title", "Titlecode", "Contentlanguage", "Contentlanguagecode",
                  "Programtheme", "Programthemecode", "Programgenre", "Programgenrecod", "Productionhouse",
                  "Prodhouse"]
    cdata_row = ["Channelname", "Title", "Contentlanguage",
                 "Programtheme", "Programgenre", "Productionhouse"]
    bn = Program.objects.filter(deleted=False).filter(channel__isnull=False)
    data = bn.values_list("channel__code", "channel__name", "title__name", "title__code", "language__name",
                          "language__code", "program_genre__program_theme__name", "program_genre__program_theme__code",
                          "program_genre__name", "program_genre__code")
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in tqdm.tqdm(data):
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:

                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
            if header_row[ind]=="Programgenrecod":
                element_sub_item.text = str(int(d)+220)
            if header_row[ind]=="Programthemecode":
                element_sub_item.text = str(int(d)+20)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task
def generate_chnmaster(output_path):
    top_txt = "BarcChannelMaster"
    header_row = ["Channel", "Channelcode", "Networkname", "Networkcode", "Language", "Languagecode", "Region",
                  "Regioncode", "Genre", "Genrecode"]
    cdata_row = ["Channel", "Networkname", "Language", "Region", "Genre"]
    bn = Channel.objects.all()
    data = []
    for b in bn:
        row_data = [
            b.name, b.code,
            b.network.name if b.network else '',
            b.network.code if b.network else '',
            b.language.name if b.language else "",
            b.language.code if b.language else "",
            b.region.name if b.region else "",
            b.region.code if b.region else "",
            b.genre.name if b.genre else "",
            b.genre.code if b.genre else "",
        ]
        data.append(row_data)
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in data:
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task
def generate_promocatmaster(output_path):
    top_txt = "BarcPromoCategoryMaster"
    header_row = ["PromoCategory", "PromoCategoryCode"]
    cdata_row = ["PromoCategory"]
    bn = PromoCategory.objects.all()
    data = []
    for b in bn:
        row_data = [
            b.name, b.code
        ]
        data.append(row_data)
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in data:
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task
def generate_genremaster(output_path):
    top_txt = "GenreMaster"
    header_row = ["PROGRAMGENRECODE", "PROGRAMGENRE", "PROGRAMTHEMECODE", "PROGRAMTHEME"]
    cdata_row = ["PROGRAMGENRE", "PROGRAMTHEME"]
    bn = ProgramGenre.objects.all()
    data = []
    for b in bn:
        row_data = [
            b.code, b.name,
            b.program_theme.code, b.program_theme.name
        ]
        data.append(row_data)
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in data:
        if str(row_data[1]).isdigit():
            continue
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])

            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
            if header_row[ind]=="PROGRAMGENRECODE":
                element_sub_item.text = str(int(d)+220)
            if header_row[ind]=="PROGRAMTHEMECODE":
                element_sub_item.text = str(int(d)+20)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task
def generate_langmaster(output_path):
    top_txt = "CURGEN"
    header_row = ["CONTENTLANGUAGECODE", "CONTENTLANGUAGE"]
    cdata_row = ["CONTENTLANGUAGE"]
    bn = ContentLanguage.objects.all()
    data = []
    for b in bn:
        row_data = [
            b.code, b.name
        ]
        data.append(row_data)
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in data:
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task
def generate_vendorbrandmaster(output_path):
    top_txt = "BarcBrandMaster"
    header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                  "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                  "Advertisinggroupcode",
                  "Descriptor", "Descriptorcode", "Id"]
    cdata_row = ["Brandname", "Title", "Brandsector",
                 "Brandcategory", "Advertiser", "Advertisinggroup",
                 "Descriptor"]
    data = Commercial.objects.all().values_list("brand_name__name","brand_name__code", "brand_name__name","brand_name__code", "brand_name__brand_category__brand_sector__name","brand_name__brand_category__brand_sector__code", "brand_name__brand_category__name","brand_name__brand_category__code","advertiser__name","advertiser__code","advertiser__advertiser_group__name","advertiser__advertiser_group__code","descriptor__text","descriptor__code", "id")
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in tqdm.tqdm(data):
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp",""))
    return True


@app.task
def generate_vendorpromomaster(output_path):
    top_txt = "BarcPromoMaster"
    header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                  "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                  "Advertisinggroupcode",
                  "Descriptor", "Descriptorcode", "Id"]
    cdata_row = ["Brandname", "Title", "Brandsector",
                 "Brandcategory", "Advertiser", "Advertisinggroup",
                 "Descriptor"]
    data = Promo.objects.all().values_list("brand_name__name", "brand_name__code", "brand_name__name",
                                                "brand_name__code", "brand_name__brand_category__brand_sector__name",
                                                "brand_name__brand_category__brand_sector__code",
                                                "brand_name__brand_category__name", "brand_name__brand_category__code",
                                                "advertiser__name", "advertiser__code",
                                                "advertiser__advertiser_group__name",
                                                "advertiser__advertiser_group__code", "descriptor__text",
                                                "descriptor__code", "id")

    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in tqdm.tqdm(data):
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task
def generate_vendorprgmaster(output_path):
    top_txt = "BarcProgramMaster"
    header_row = ["Channelnamecode", "Channelname", "Title", "Titlecode", "Contentlanguage", "Contentlanguagecode",
                  "Programtheme", "Programthemecode", "Programgenre", "Programgenrecod", "Productionhouse",
                  "Prodhouse", "Id"]
    cdata_row = ["Channelname", "Title", "Contentlanguage",
                 "Programtheme", "Programgenre", "Productionhouse"]
    bn = Program.objects.all().filter(channel__isnull=False)
    data = bn.values_list("channel__code", "channel__name", "title__name", "title__code", "language__name",
                          "language__code", "program_genre__program_theme__name", "program_genre__program_theme__code",
                          "program_genre__name", "program_genre__code", "prod_house__name", "prod_house__code", "id")
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in tqdm.tqdm(data):
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task
def generate_vendorchnmaster(output_path):
    top_txt = "BarcChannelMaster"
    header_row = ["Channel", "Channelcode", "Networkname", "Networkcode", "Language", "Languagecode", "Region",
                  "Regioncode", "Genre", "Genrecode", "Id"]
    cdata_row = ["Channel", "Networkname", "Language", "Region", "Genre"]
    bn = Channel.objects.all()
    data = []
    for b in bn:
        row_data = [
            b.name, b.code,
            b.network.name if b.network else '',
            b.network.code if b.network else '',
            b.language.name if b.language else "",
            b.language.code if b.language else "",
            b.region.name if b.region else "",
            b.region.code if b.region else "",
            b.genre.name if b.genre else "",
            b.genre.code if b.genre else "",
            b.id
        ]
        data.append(row_data)
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in data:
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task
def generate_vendorpromocatmaster(output_path):
    top_txt = "BarcPromoCategoryMaster"
    header_row = ["PromoCategory", "PromoCategoryCode", "Id"]
    cdata_row = ["PromoCategory"]
    bn = PromoCategory.objects.all()
    data = []
    for b in bn:
        row_data = [
            b.name, b.code, b.id
        ]
        data.append(row_data)
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in data:
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task
def generate_vendorgenremaster(output_path):
    top_txt = "GenreMaster"
    header_row = ["PROGRAMGENRECODE", "PROGRAMGENRE", "PROGRAMTHEMECODE", "PROGRAMTHEME", "Id"]
    cdata_row = ["PROGRAMGENRE", "PROGRAMTHEME"]
    bn = ProgramGenre.objects.all()
    data = []
    for b in bn:
        row_data = [
            b.code, b.name,
            b.program_theme.code, b.program_theme.name,
            b.id
        ]
        data.append(row_data)
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in data:
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task
def generate_vendorlangmaster(output_path):
    top_txt = "CURGEN"
    header_row = ["CONTENTLANGUAGECODE", "CONTENTLANGUAGE", "Id"]
    cdata_row = ["CONTENTLANGUAGE"]
    bn = ContentLanguage.objects.all()
    data = []
    for b in bn:
        row_data = [
            b.code, b.name, b.id
        ]
        data.append(row_data)
    main_top = ET.Element(top_txt)
    main_tree = ET.ElementTree(main_top)
    for row_data in data:
        item = ET.SubElement(main_top, 'Item')
        keys = []
        for ind, d in enumerate(row_data):
            element_sub_item = ET.SubElement(item, header_row[ind])
            if d:
                element_sub_item.text = str(d)
            else:
                element_sub_item.text = ''
            if header_row[ind] in cdata_row:
                element_sub_item.text = ET.CDATA(element_sub_item.text)
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    upload_file(output_path, "barc-playout-files", output_path.replace("/tmp", ""))
    return True


@app.task(name='super_task.error_callback')
def error_callback(*args, **kwargs):
    print('error_callback')
    print(args)
    print(kwargs)
    return 'error'

@app.task
def generate_reports(date, id=None):
    clean_up()
    shutil.rmtree('/tmp/reports')
    check_or_create_file('/tmp/reports/tmp.txt')
    vendors = ["TAM", "PFT"]
    subtasks = []
    for vendor in vendors:
        vendor_tasks = repurposeVendorReport("barc-playout-files", "Daily_Tam_Tabsons_Files/{}/{}".format(vendor,date))
        subtasks += vendor_tasks
    all_report_tasks = chord(subtasks)(zip_reports.s(date, id).set(link_error=['super_task.error_callback']))
    return all_report_tasks


@app.task
def generate_custom_reports(date, headers):
    clean_up()
    shutil.rmtree('/tmp/customreports')
    check_or_create_file('/tmp/customreports/tmp.txt')
    vendors = ["TAM", "PFT"]
    subtasks = []
    for vendor in vendors:
        vendor_tasks = repurposeVendorCustomReport("barc-playout-files", "Daily_Tam_Tabsons_Files/{}/{}".format(vendor,date), headers)
        subtasks += vendor_tasks
    chord(subtasks)(zip_custom_reports.s(date)).get()
    return True


@app.task
def zip_finalmasters(date):
    dobj = datetime.datetime.strptime(date, '%Y%m%d')
    ndate = dobj.strftime('%Y-%m-%d')
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket("barc-playout-files")
    for object in bucket.objects.filter(Prefix="/masters/"):
        path = os.path.join("/tmp", object.key)
        output_path = os.path.join("/tmp/masters", os.path.basename(path))
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        s3_resource.meta.client.download_file("barc-playout-files", object.key, output_path)
    shutil.make_archive("/tmp/masters/BARC_MasterReportsXmls_{}".format(date), "zip", "/tmp/masters")
    upload_file("/tmp/masters/BARC_MasterReportsXmls_{}".format(date), "barc-playout-files",
                "supermaster/{}/BARC_MasterReportsXmls_{}.zip".format(ndate,date))

@app.task
def zip_finalreports(date):
    dobj = datetime.datetime.strptime(date, '%Y%m%d')
    ndate = dobj.strftime('%Y-%m-%d')
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket("barc-playout-files")
    for object in bucket.objects.filter(Prefix="/reports/"):
        path = os.path.join("/tmp", object.key)
        output_path = os.path.join("/tmp/reports", os.path.basename(path))
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        s3_resource.meta.client.download_file("barc-playout-files", object.key, output_path)
    shutil.make_archive("/tmp/reports/BARC_ChannelReportsXmls_{}".format(date), "zip", "/tmp/masters")
    upload_file("/tmp/masters/BARC_ChannelReportsXmls_{}".format(date), "barc-playout-files",
                "supermaster/{}/BARC_ChannelReportsXmls_{}".format(ndate,date))


@app.task
def match_videos(ven, date):
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket("barc-playout-files")
    remoteDirectoryName="Videos/{}/{}/".format(ven, date)
    for object in bucket.objects.filter(Prefix=remoteDirectoryName):
        path = os.path.join("/tmp", object.key)
        file_name = os.path.basename(path)
        id = file_name.split("_")[0]
        print(object.key)
        # output_path = os.path.join("/tmp/videos/", os.path.basename(path))
        if "masters" not in object.key and "mp4" in object.key:

            url = "https://barc-playout-files.s3.ap-south-1.amazonaws.com/"+object.key
            v = Video.objects.create(title=file_name, file=url)
            vc = VendorCommercial.objects.filter(id=id).first()
            if vc:
                # print(">>>>>>>>>>>>>>>>>>>>>>>>HIT IN>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                # print(object.key)
                # print("<<<<<<<<<<<<<<<<<<<<<<<<<HIT OUT<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                vc.video.add(v)
                vc.save()
            vp = VendorPromo.objects.filter(id=id).first()
            if vp:
                # print(">>>>>>>>>>>>>>>>>>>>>>>>HIT IN>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                # print(object.key)
                # print("<<<<<<<<<<<<<<<<<<<<<<<<<HIT OUT<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                vp.video.add(v)
                vp.save()