import tqdm
import sys, csv
from tags.models import *
from django.db.utils import IntegrityError

def load_channel(channel_master):
    with open(channel_master, newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        lines = []
        channel_network = []
        channel_name = []
        content_language = []
        region = []
        genre = []
        count = 0
        skip = 0
        for row in spamreader:
            if skip <1:
                skip+=1
            else:
                try:
                    lines.append(row)
                    if row[0:2] not in channel_name:
                        channel_name.append(row[0:2])

                    if row[2:4] not in channel_network:
                        channel_network.append(row[2:4])
                    c_net_obj, c = ChannelNetwork.objects.get_or_create(name=row[2], code=int(row[3]))
                    if row[4:6] not in content_language:
                        content_language.append(row[4:6])
                    c_lang_obj, c = ContentLanguage.objects.get_or_create(name=row[4], code=int(row[5]))

                    if row[6:8] not in region:
                        region.append(row[6:8])
                    r_obj, c = Region.objects.get_or_create(name=row[6], code=int(row[7]))

                    if row[8:10] not in genre:
                        genre.append(row[8:10])
                    c_gnr_obj, c = ChannelGenre.objects.get_or_create(name=row[8], code=int(row[9]))

                    ch_obj, c = Channel.objects.get_or_create(name=row[0], code=row[1], language=c_lang_obj, abbr="",
                                                              network=c_net_obj, genre=c_gnr_obj, region=r_obj)
                    if c:
                        count +=1
                except IntegrityError:
                    print(row)
                    pass
                except ValueError:
                    print("Value Error")
                    print(row)
                    pass
    print(count)


def load_commercial(channel_master):
    with open(channel_master, newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        lines = []
        count = 0
        skip = 0
        for row in tqdm.tqdm(spamreader):
            if skip <1:
                skip+=1
            else:
                try:
                    lines.append(row)
                    b_sec_obj, c = BrandSector.objects.get_or_create(name=row[4], code=int(row[5]))
                    b_cat_obj, c = BrandCategory.objects.get_or_create(name=row[6], code=int(row[7]),
                                                                       brand_sector=b_sec_obj)
                    b_name_obj, c = BrandName.objects.get_or_create(name=row[0], code=int(row[1]),
                                                                    brand_category=b_cat_obj)
                    title_obj, c = Title.objects.get_or_create(name=row[2], code=int(row[3]))
                    adv_grp_obj, c = AdvertiserGroup.objects.get_or_create(name=row[10], code=int(row[11]))
                    adv_obj, c = Advertiser.objects.get_or_create(name=row[8], code=int(row[9]),
                                                                  advertiser_group=adv_grp_obj)
                    des_obj, c = Descriptor.objects.get_or_create(text=row[12], code=int(row[13]))

                    ch_obj, c = Commercial.objects.get_or_create(title=title_obj, brand_name=b_name_obj,
                                                                 descriptor=des_obj, advertiser=adv_obj)
                    if c:
                        count +=1
                except IntegrityError:
                    # print(row)
                    pass
                except ValueError:
                    # print("Value Error")
                    # print(row)
                    pass
    print(count)


def load_program(channel_master):
    with open(channel_master, newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        lines = []
        count = 0
        skip = 0
        for row in tqdm.tqdm(spamreader):
            if skip <1:
                skip+=1
            else:
                try:
                    lines.append(row)
                    title_obj, c = Title.objects.get_or_create(name=row[2], code=int(row[3]))
                    c_lang_obj, c = ContentLanguage.objects.get_or_create(name=row[4], code=int(row[5]))
                    chn_obj, c = Channel.objects.get_or_create(name=row[1], code=int(row[0]))
                    prog_thm_obj, c = ProgramTheme.objects.get_or_create(name=row[6], code=int(row[7]))
                    prog_gnr_obj, c = ProgramGenre.objects.get_or_create(name=row[8], code=int(row[9]),
                                                                         program_theme=prog_thm_obj)
                    prod_house_obj, c = ProductionHouse.objects.get_or_create(name=row[10], code=int(row[11]))
                    prog_obj, c = Program.objects.get_or_create(title=title_obj, language=c_lang_obj,
                                                                program_genre=prog_gnr_obj, channel= chn_obj,
                                                                prod_house=prod_house_obj)
                    if c:
                        count +=1
                except IntegrityError:
                    # print(row)
                    pass
                except ValueError:
                    # print("Value Error")
                    # print(row)
                    pass
    print(count)


def load_promo(channel_master):
    with open(channel_master, newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        lines = []
        count = 0
        skip = 0
        for row in tqdm.tqdm(spamreader):
            if skip <1:
                skip+=1
            else:
                try:
                    lines.append(row)
                    # title_obj, c = Title.objects.get_or_create(name=row[2], code=int(row[3]))
                    b_sec_obj, c = BrandSector.objects.get_or_create(name=row[4], code=int(row[5]))
                    b_cat_obj, c = BrandCategory.objects.get_or_create(name=row[6], code=int(row[7]),
                                                                       brand_sector=b_sec_obj)
                    b_name_obj, c = BrandName.objects.get_or_create(name=row[0], code=int(row[1]),
                                                                    brand_category=b_cat_obj)
                    adv_grp_obj, c = AdvertiserGroup.objects.get_or_create(name=row[10], code=int(row[11]))

                    if int(row[11]):
                        adv_obj, c = Advertiser.objects.get_or_create(name=row[8], code=int(row[9]),
                                                                      advertiser_group=adv_grp_obj)
                    else:
                        adv_obj, c = Advertiser.objects.get_or_create(name=row[8], code=int(row[9]))
                    des_obj, c = Descriptor.objects.get_or_create(text=row[12], code=int(row[13]))

                    prm_obj, c = Promo.objects.get_or_create(title=None, channel=None, promo_channel=None,
                                                             brand_name=b_name_obj,
                                                             advertiser=adv_obj, descriptor=des_obj)
                    if c:
                        count +=1
                except IntegrityError:
                    pass
                except ValueError:
                    pass
    print(count)