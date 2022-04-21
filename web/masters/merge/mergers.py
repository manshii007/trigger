from masters.models import VendorProgram, VendorPromo,  VendorCommercial

from tags.models import ProgramGenre, ProgramTheme, BrandCategory, BrandName, BrandSector, Advertiser, AdvertiserGroup, Descriptor, Title, ContentLanguage, ProductionHouse, Promo, Program, Commercial
from django.db import IntegrityError
from django.core.exceptions import MultipleObjectsReturned

import tqdm
from masters.tasks import similar_commercial


def merge_promo(list_ids=None):
    vendor_promos = VendorPromo.objects.filter(is_mapped=True, promo=None)
    titles = []
    title_tmp = []
    brand_sectors = []
    brand_sector_tmp = []
    advertiser_groups = []
    advertiser_group_tmp = []
    descriptors = []
    descriptor_tmp = []
    all_titles = [x['name'] for x in Title.objects.all().values('name').distinct()]
    all_brand_sectors = [x['name'] for x in BrandSector.objects.all().values('name').distinct()]
    all_advertiser_groups = [x['name'] for x in AdvertiserGroup.objects.all().values('name').distinct()]
    all_descriptors = [x['text'] for x in Descriptor.objects.all().values('text').distinct()]
    for vc in tqdm.tqdm(vendor_promos):
        try:
            if vc.title not in all_titles and vc.title not in title_tmp:
                titles.append(Title(name=vc.title))
                title_tmp.append(vc.title)

            if vc.brand_sector not in all_brand_sectors and vc.brand_sector not in brand_sector_tmp:
                brand_sectors.append(BrandSector(name=vc.brand_sector))
                brand_sector_tmp.append(vc.brand_sector)

            if vc.advertiser_group not in all_advertiser_groups and vc.advertiser_group not in advertiser_group_tmp:
                advertiser_groups.append(AdvertiserGroup(name=vc.advertiser_group))
                advertiser_group_tmp.append(vc.advertiser_group)

            if vc.descriptor not in all_descriptors and vc.descriptor not in descriptor_tmp:
                descriptors.append(Descriptor(text=vc.descriptor))
                descriptor_tmp.append(vc.descriptor)

            if len(titles) > 5000:
                n = Title.objects.bulk_create(titles)
                titles = []
            if len(advertiser_groups) > 5000:
                n = AdvertiserGroup.objects.bulk_create(advertiser_groups)
                advertiser_groups = []
            if len(brand_sectors) > 5000:
                n = BrandSector.objects.bulk_create(brand_sectors)
                brand_sectors = []
            if len(descriptors) > 5000:
                n = Descriptor.objects.bulk_create(descriptors)
                descriptors = []
        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned  as e:
            print(vc.id)
            print(e)
            pass

    n = Title.objects.bulk_create(titles)
    n = BrandSector.objects.bulk_create(brand_sectors)
    n = AdvertiserGroup.objects.bulk_create(advertiser_groups)
    n = Descriptor.objects.bulk_create(descriptors)

    brand_categorys = []
    advertisers = []
    for vc in tqdm.tqdm(vendor_promos):
        try:
            brand_sector = BrandSector.objects.filter(name=vc.brand_sector).first()
            brand_category = BrandCategory.objects.filter(name=vc.brand_category, brand_sector=brand_sector).first()
            if not brand_category:
                brand_categorys.append(BrandCategory(name=vc.brand_category, brand_sector=brand_sector))

            if len(brand_categorys) > 5000:
                n = BrandCategory.objects.bulk_create(brand_categorys)
                brand_categorys = []

            advertiser_group = AdvertiserGroup.objects.filter(name=vc.advertiser_group).first()
            advertiser = Advertiser.objects.filter(name=vc.advertiser, advertiser_group=advertiser_group).first()
            if not advertiser:
                advertisers.append(Advertiser(name=vc.advertiser, advertiser_group=advertiser_group))

            if len(brand_categorys) > 5000:
                n = Advertiser.objects.bulk_create(advertisers)
                advertisers = []
        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned  as e:
            print(vc.id)
            print(e)
            pass
    n = BrandCategory.objects.bulk_create(brand_categorys)
    n = Advertiser.objects.bulk_create(advertisers)

    brand_names = []
    for vc in tqdm.tqdm(vendor_promos):
        try:
            brand_category = BrandCategory.objects.filter(name=vc.brand_category, brand_sector=brand_sector).first()
            brand_name = BrandName.objects.filter(name=vc.brand_name, brand_category=brand_category)
            if not brand_name:
                brand_names.append(BrandName(name=vc.brand_name, brand_category=brand_category))

            if len(brand_names) > 5000:
                n = BrandName.objects.bulk_create(brand_names)
                brand_names = []

        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned  as e:
            print(vc.id)
            print(e)
            pass
    n = BrandName.objects.bulk_create(brand_names)

    super_commercials = []
    keys = []
    super_commercials_obj = Promo.objects.all().values("title__name").distinct()
    for st in super_commercials_obj:
        k_tmp = ",".join([st['title__name']])
        keys.append(k_tmp)
    for vc in tqdm.tqdm(vendor_promos):
        try:

            k = [vc.title]
            k = [str(kt) for kt in k]
            key = ','.join(k)
            if key not in keys and vc.channel:
                title = Title.objects.filter(name=vc.title).first()
                brand_name = BrandName.objects.filter(name=vc.brand_name).first()
                descriptor = Descriptor.objects.filter(text=vc.descriptor).first()
                advertiser = Advertiser.objects.filter(name=vc.advertiser).first()
                super_commercials.append(Promo(title=title, brand_name=brand_name, descriptor=descriptor,
                                               advertiser=advertiser))
                keys.append(key)
            if len(super_commercials) > 5000:
                n = Promo.objects.bulk_create(super_commercials)
                super_commercials = []

        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned  as e:
            print(vc.id)
            print(e)
            pass

    n = Promo.objects.bulk_create(super_commercials)

    for vc in tqdm.tqdm(vendor_promos):
        try:
            title = Title.objects.filter(name=vc.title).first()

            super_commercial = Promo.objects.filter(title=title).first()
            vc.super_commercial = super_commercial
            vc.save()
        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned as e:
            print(vc.id)
            print(e)
            pass


def merge_commercials(list_ids=None):
    vendor_commercials = VendorCommercial.objects.filter(is_mapped=True, commercial=None)
    brand_sectors = []
    brand_sector_tmp = []
    advertiser_groups = []
    advertiser_group_tmp = []
    descriptors = []
    descriptor_tmp = []
    all_brand_sectors = [x['name'] for x in BrandSector.objects.all().values('name').distinct()]
    all_advertiser_groups = [x['name'] for x in AdvertiserGroup.objects.all().values('name').distinct()]
    all_descriptors = [x['text'] for x in Descriptor.objects.all().values('text').distinct()]
    for vc in tqdm.tqdm(vendor_commercials):
        try:
            if vc.brand_sector not in all_brand_sectors and vc.brand_sector not in brand_sector_tmp:
                brand_sectors.append(BrandSector(name=vc.brand_sector))
                brand_sector_tmp.append(vc.brand_sector)

            if vc.advertiser_group not in all_advertiser_groups and vc.advertiser_group not in advertiser_group_tmp:
                advertiser_groups.append(AdvertiserGroup(name=vc.advertiser_group))
                advertiser_group_tmp.append(vc.advertiser_group)

            if vc.descriptor not in all_descriptors and vc.descriptor not in descriptor_tmp:
                descriptors.append(Descriptor(text=vc.descriptor))
                descriptor_tmp.append(vc.descriptor)

            if len(advertiser_groups) > 5000:
                n = AdvertiserGroup.objects.bulk_create(advertiser_groups)
                advertiser_groups = []
            if len(brand_sectors) > 5000:
                n = BrandSector.objects.bulk_create(brand_sectors)
                brand_sectors = []
            if len(descriptors) > 5000:
                n = Descriptor.objects.bulk_create(descriptors)
                descriptors = []
        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned  as e:
            print(vc.id)
            print(e)
            pass

    n = BrandSector.objects.bulk_create(brand_sectors)
    n = AdvertiserGroup.objects.bulk_create(advertiser_groups)
    n = Descriptor.objects.bulk_create(descriptors)

    brand_categorys = []
    advertisers = []
    for vc in tqdm.tqdm(vendor_commercials):
        try:
            brand_sector = BrandSector.objects.filter(name=vc.brand_sector).first()
            brand_category = BrandCategory.objects.filter(name=vc.brand_category, brand_sector=brand_sector).first()
            if not brand_category:
                brand_categorys.append(BrandCategory(name=vc.brand_category, brand_sector=brand_sector))

            if len(brand_categorys) > 5000:
                n = BrandCategory.objects.bulk_create(brand_categorys)
                brand_categorys = []

            advertiser_group = AdvertiserGroup.objects.filter(name=vc.advertiser_group).first()
            advertiser = Advertiser.objects.filter(name=vc.advertiser, advertiser_group=advertiser_group).first()
            if not advertiser:
                advertisers.append(Advertiser(name=vc.advertiser, advertiser_group=advertiser_group))

            if len(brand_categorys) > 5000:
                n = Advertiser.objects.bulk_create(advertisers)
                advertisers = []
        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned  as e:
            print(vc.id)
            print(e)
            pass
    n = BrandCategory.objects.bulk_create(brand_categorys)
    n = Advertiser.objects.bulk_create(advertisers)

    brand_names = []
    for vc in tqdm.tqdm(vendor_commercials):
        try:
            brand_category = BrandCategory.objects.filter(name=vc.brand_category, brand_sector=brand_sector).first()
            brand_name = BrandName.objects.filter(name=vc.brand_name, brand_category=brand_category)
            if not brand_name:
                brand_names.append(BrandName(name=vc.brand_name, brand_category=brand_category))

            if len(brand_names) > 5000:
                n = BrandName.objects.bulk_create(brand_names)
                brand_names = []

        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned  as e:
            print(vc.id)
            print(e)
            pass
    n = BrandName.objects.bulk_create(brand_names)

    super_commercials = []
    keys = []
    super_commercials_obj = Commercial.objects.all().values("brand_name__name", "descriptor__text").distinct()
    for st in super_commercials_obj:
        k_tmp = ",".join([st['brand_name__name'], st['descriptor__text']])
        keys.append(k_tmp)
    for vc in tqdm.tqdm(vendor_commercials):
        try:

            k = [vc.brand_name, vc.descriptor]
            k = [str(kt) for kt in k]
            key = ','.join(k)
            if key not in keys:
                brand_name = BrandName.objects.filter(name=vc.brand_name).first()
                descriptor = Descriptor.objects.filter(text=vc.descriptor).first()
                advertiser = Advertiser.objects.filter(name=vc.advertiser).first()
                super_commercials.append(Commercial(brand_name=brand_name, descriptor=descriptor,
                                                    advertiser=advertiser))
                keys.append(key)
            if len(super_commercials) > 5000:
                n = Commercial.objects.bulk_create(super_commercials)
                super_commercials = []

        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned  as e:
            print(vc.id)
            print(e)
            pass

    n = Commercial.objects.bulk_create(super_commercials)

    for vc in tqdm.tqdm(vendor_commercials):
        try:
            brand_name = BrandName.objects.filter(name=vc.brand_name).first()
            descriptor = Descriptor.objects.filter(text=vc.descriptor).first()

            super_commercial = Commercial.objects.filter(brand_name=brand_name, descriptor=descriptor).first()
            vc.commercial = super_commercial
            vc.save()
        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except AttributeError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned as e:
            print(vc.id)
            print(e)
            pass


def merge_commercial(ids=None):

    qs = VendorCommercial.objects.filter(id__in=ids)
    vc = VendorCommercial.objects.filter(id=ids[0]).first()
    # try:
    brand_sector, c = BrandSector.objects.get_or_create(name=vc.brand_sector)

    brand_category, c = BrandCategory.objects.get_or_create(name=vc.brand_category,
                                                            brand_sector=brand_sector)

    brand_name, c = BrandName.objects.get_or_create(name=vc.brand_name, brand_category=brand_category)

    title = Title.objects.filter(name=vc.title).first()
    if not title:
        title = Title.objects.create(name=vc.title)

    advertiser_group, c = AdvertiserGroup.objects.get_or_create(name=vc.advertiser_group)

    advertiser, c = Advertiser.objects.get_or_create(name=vc.advertiser, advertiser_group=advertiser_group)

    descriptor = Descriptor.objects.filter(text=vc.descriptor).first()
    if not descriptor:
        descriptor = Descriptor.objects.create(text=vc.descriptor)

    super_commercial, c = Commercial.objects.get_or_create(title=title, brand_name=brand_name,
                                                           advertiser=advertiser,
                                                           descriptor=descriptor)
    qs.update(commercial=super_commercial, is_mapped=True)
    for q in qs:
        similar_commercial.delay(q.id)


def merge_program(list_ids=None):
    vendor_programs = VendorProgram.objects.filter(is_mapped=True, super_program=None)
    titles = []
    title_tmp = []
    program_themes = []
    program_themes_tmp = []
    languages = []
    languages_tmp = []
    prod_houses = []
    prod_houses_tmp = []
    program_genres = []
    all_titles =[x['name'] for x in Title.objects.all().values('name').distinct()]
    all_program_theme = [x['name'] for x in ProgramTheme.objects.all().values('name').distinct()]
    all_languages = [x['name'] for x in ContentLanguage.objects.all().values('name').distinct()]
    all_prod_houses = [x['name'] for x in ProductionHouse.objects.all().values('name').distinct()]
    for vc in tqdm.tqdm(vendor_programs):
        try:

            if vc.title not in all_titles and vc.title not in title_tmp:
                titles.append(Title(name=vc.title))
                title_tmp.append(vc.title)

            if vc.program_theme not in all_program_theme and vc.program_theme not in program_themes_tmp:
                program_themes.append(ProgramTheme(name=vc.program_theme))
                program_themes_tmp.append(vc.program_theme)

            if vc.language not in all_languages and vc.language not in languages_tmp:
                languages.append(ContentLanguage(name=vc.language))
                languages_tmp.append(vc.language)
            if vc.prod_house:
                if vc.prod_house not in all_prod_houses and vc.prod_house not in prod_houses_tmp:
                    prod_houses.append(ProductionHouse(name=vc.prod_house))
                    prod_houses_tmp.append(vc.prod_house)

            if len(titles)>2000:
                n = Title.objects.bulk_create(titles)
                titles = []
            if len(program_themes)>2000:
                n = ProgramTheme.objects.bulk_create(program_themes)
                program_themes = []
            if len(languages)>2000:
                n = ContentLanguage.objects.bulk_create(languages)
                languages = []
            if len(prod_houses)>2000:
                n = ProductionHouse.objects.bulk_create(prod_houses)
                prod_houses = []
        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned  as e:
            print(vc.id)
            print(e)
            pass

    n = Title.objects.bulk_create(titles)
    n = ProgramTheme.objects.bulk_create(program_themes)
    n = ContentLanguage.objects.bulk_create(languages)
    n = ProductionHouse.objects.bulk_create(prod_houses)

    for vc in tqdm.tqdm(vendor_programs):
        try:
            program_theme = ProgramTheme.objects.filter(name=vc.program_theme).first()
            program_genre = ProgramGenre.objects.filter(name=vc.program_genre, program_theme=program_theme).first()
            if not program_genre:
                program_genres.append(ProgramGenre(name=vc.program_genre, program_theme=program_theme))

            if len(program_genres)>2000:
                n = ProgramGenre.objects.bulk_create(program_genres)
                program_genres = []

        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned  as e:
            print(vc.id)
            print(e)
            pass
    n = ProgramGenre.objects.bulk_create(program_genres)
    super_programs = []
    keys = []
    super_programs_obj = Program.objects.all().values("title__name","program_genre__name", "language__name").distinct()
    for st in super_programs_obj:
        k_tmp = ",".join([st['title__name'], st['program_genre__name'], st['language__name']])
        keys.append(k_tmp)
    for vc in tqdm.tqdm(vendor_programs):
        try:

            k = [vc.title,vc.program_genre,vc.language]
            k = [str(kt) for kt in k]
            key = ','.join(k)
            if key not in keys and vc.channel:
                title = Title.objects.filter(name=vc.title).first()
                program_theme = ProgramTheme.objects.filter(name=vc.program_theme).first()
                language = ContentLanguage.objects.filter(name=vc.language).first()

                if vc.prod_house:
                    prod_house = ProductionHouse.objects.filter(name=vc.prod_house).first()
                else:
                    prod_house = None

                program_genre = ProgramGenre.objects.filter(name=vc.program_genre, program_theme=program_theme).first()
                super_programs.append(Program(title=title, program_genre=program_genre,
                                              language=language, prod_house=prod_house,
                                              channel=vc.channel))
                keys.append(key)
            if len(super_programs)>2000:
                n = Program.objects.bulk_create(super_programs)
                super_programs = []

        except KeyError:
            print(vc.id)
            pass
        except IntegrityError as e:
            print(vc.id)
            print(e)
            pass
        except MultipleObjectsReturned  as e:
            print(vc.id)
            print(e)
            pass

        n = Program.objects.bulk_create(super_programs)

        for vc in tqdm.tqdm(vendor_programs):
            try:
                title = Title.objects.filter(name=vc.title).first()
                program_theme = ProgramTheme.objects.filter(name=vc.program_theme).first()
                language = ContentLanguage.objects.filter(name=vc.language).first()

                if vc.prod_house:
                    prod_house = ProductionHouse.objects.filter(name=vc.prod_house).first()
                else:
                    prod_house = None

                program_genre = ProgramGenre.objects.filter(name=vc.program_genre, program_theme=program_theme).first()
                super_program = Program.objects.filter(title=title, program_genre=program_genre,
                                                       language=language, prod_house=prod_house,
                                                       channel=vc.channel).first()
                vc.super_program = super_program
                vc.save()
            except KeyError:
                print(vc.id)
                pass
            except IntegrityError as e:
                print(vc.id)
                print(e)
                pass
            except MultipleObjectsReturned  as e:
                print(vc.id)
                print(e)
                pass
