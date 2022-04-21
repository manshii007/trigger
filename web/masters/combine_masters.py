import argparse
import glob
import os
import tqdm
from xml.etree import ElementTree
from lxml import etree as ET
import errno, random, subprocess
from shutil import copyfile
import uuid


def check_or_create_file(file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


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


def process(dir=None):

    source_masters = os.path.join(dir, 'source', 'masters', '*.xml')
    feeder_masters = os.path.join(dir, 'feeder1', 'masters', '*.xml')
    # feeder2_masters = os.path.join(args.dir, 'feeder2', 'masters', '*.xml')

    for file_path in tqdm.tqdm(glob.glob(source_masters)):
        brand_keys = []
        promo_keys = []
        program_keys = []
        genre_keys = []
        print(file_path)
        tmp_tmp = file_path + ".tmp"
        subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, file_path])
        subprocess.run(["mv", tmp_tmp, file_path])
        output_path = os.path.join(dir, 'converted', 'masters', os.path.basename(file_path))
        check_or_create_file(output_path)
        top_txt = ""

        reseed = ["Brandnamecode", "Titlecode", "Brandsectorcode", "Brandcategorycode", "Advertisercode",
                  "Advertisinggroupcode",
                  "Descriptorcode", "Programgenrecode", "Programthemecode", "Programgenrecod", "PROGRAMGENRECODE",
                  "PROGRAMTHEMECODE"]

        low_reseed = ["advertisinggroupcode", "programgenrecode", "programthemecode", "programgenrecod"]

        if "Brand" in os.path.basename(file_path):
            top_txt ="BarcBrandMaster"
            header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                          "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                          "Advertisinggroupcode",
                          "Descriptor", "Descriptorcode"]
            cdata_row = ["Brandname", "Title", "Brandsector",
                         "Brandcategory", "Advertiser", "Advertisinggroup",
                         "Descriptor"]
        elif "PromoMst" in os.path.basename(file_path):
            top_txt ="BarcPromoMaster"
            header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                          "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                          "Advertisinggroupcode",
                          "Descriptor", "Descriptorcode"]
            cdata_row = ["Brandname", "Title", "Brandsector",
                         "Brandcategory", "Advertiser", "Advertisinggroup",
                         "Descriptor"]
        elif "PrgMst" in os.path.basename(file_path):
            top_txt ="BarcProgramMaster"
            header_row = ["Channelnamecode", "Channelname", "Title", "Titlecode", "Contentlanguage", "Contentlanguagecode",
                          "Programtheme", "Programthemecode", "Programgenre", "Programgenrecod", "Productionhouse",
                          "Prodhouse"]
            cdata_row = ["Channelname", "Title", "Contentlanguage",
                          "Programtheme", "Programgenre", "Productionhouse"]
        elif "ChnMst" in os.path.basename(file_path):
            top_txt="BarcChannelMaster"
            header_row = ["Channel", "Channelcode", "Networkname", "Networkcode", "Language", "Languagecode", "Region",
                          "Regioncode", "Genre", "Genrecode"]
            cdata_row = ["Channel", "Networkname", "Language", "Region", "Genre"]
        elif "PromoCategory" in os.path.basename(file_path):
            top_txt="BarcPromoCategoryMaster"
            header_row = ["PromoCategory", "PromoCategoryCode"]
            cdata_row = ["PromoCategory"]
        elif "Genre" in os.path.basename(file_path): # pft different
            top_txt="GenreMaster"
            header_row = ["PROGRAMGENRECODE", "PROGRAMGENRE", "PROGRAMTHEMECODE", "PROGRAMTHEME"]
            cdata_row = ["PROGRAMGENRE", "PROGRAMTHEME"]
        elif "Content" in os.path.basename(file_path): # pft different
            top_txt = "CURGEN"
            header_row = ["CONTENTLANGUAGECODE", "CONTENTLANGUAGE"]
            cdata_row = ["CONTENTLANGUAGE"]
        else:
            copyfile(file_path, output_path)
            continue
        tree = ElementTree.parse(file_path)
        root = tree.getroot()
        data = []
        for child in root:
            row_data = []
            for gc in child:
                    row_data.append(gc.text)
            data.append(row_data)
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
                if header_row[ind] in reseed and d and header_row[ind].lower() not in low_reseed:
                    random.seed(d)
                    element_sub_item.text = str(random.getrandbits(29))
                    keys.append(d)
                elif header_row[ind] in reseed and d and header_row[ind].lower() in low_reseed:
                    random.seed(d)
                    element_sub_item.text = str(random.getrandbits(12))
                    keys.append(d)
            if "Brand" in os.path.basename(file_path):
                brand_keys.append('---'.join(keys))
            elif "PrgMst" in os.path.basename(file_path):
                program_keys.append('---'.join(keys))
            elif "PromoMst" in os.path.basename(file_path):
                promo_keys.append('---'.join(keys))
            elif "Genre" in os.path.basename(file_path):
                genre_keys.append('---'.join(keys))

            element_sub_item = ET.SubElement(item, "Id")
            element_sub_item.text = str(uuid.uuid4())

        brand_keys = set(brand_keys)
        promo_keys = set(promo_keys)
        program_keys = set(program_keys)
        genre_keys = set(genre_keys)

        feeder_path = file_path.replace("source", "feeder1")
        tmp_tmp = feeder_path + ".tmp"
        subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, feeder_path])
        subprocess.run(["mv", tmp_tmp, feeder_path])

        if "Brand" in os.path.basename(feeder_path):
            header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                          "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                          "Advertisinggroupcode",
                          "Descriptor", "Descriptorcode"]
            cdata_row = ["Brandname", "Title", "Brandsector",
                         "Brandcategory", "Advertiser", "Advertisinggroup",
                         "Descriptor"]
        elif "PromoMst" in os.path.basename(feeder_path):
            header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                          "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                          "Advertisinggroupcode",
                          "Descriptor", "Descriptorcode"]
            cdata_row = ["Brandname", "Title", "Brandsector",
                         "Brandcategory", "Advertiser", "Advertisinggroup",
                         "Descriptor"]
        elif "PrgMst" in os.path.basename(feeder_path):
            header_row = ["Channelnamecode", "Channelname", "Title", "Titlecode", "Contentlanguage",
                          "Contentlanguagecode",
                          "Programtheme", "Programthemecode", "Programgenre", "Programgenrecod", "Productionhouse",
                          "Prodhouse"]
            cdata_row = ["Channelname", "Title", "Contentlanguage",
                         "Programtheme", "Programgenre", "Productionhouse"]
        # elif "ChnMst" in os.path.basename(file_path):
        #     header_row = ["Channel", "Channelcode", "Networkname", "Networkcode", "Language", "Languagecode", "Region",
        #                   "Regioncode", "Genre", "Genrecode"]
        #     cdata_row = ["Channel", "Networkname", "Language", "Region", "Genre"]
        # elif "PromoCategory" in os.path.basename(file_path):
        #     header_row = ["PromoCategory", "PromoCategoryCode"]
        #     cdata_row = ["PromoCategory"]
        elif "Genre" in os.path.basename(file_path):
            header_row = ["PROGRAMGENRECODE", "PROGRAMGENRE", "PROGRAMTHEMECODE", "PROGRAMTHEME"]
            cdata_row = ["PROGRAMGENRE", "PROGRAMTHEME"]
        # elif "Content" in os.path.basename(file_path):
        #     header_row = ["CONTENTLANGUAGECODE", "CONTENTLANGUAGE"]
        #     cdata_row = ["CONTENTLANGUAGE"]
        else:
            indent(main_top)
            with open(output_path, 'wb') as xml_file:
                main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
            continue
        tree = ElementTree.parse(feeder_path)
        root = tree.getroot()
        data = []
        for child in root:
            row_data = []
            for gc in child:
                row_data.append(gc.text)
            data.append(row_data)

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
                if header_row[ind] in reseed and d and header_row[ind].lower() not in low_reseed:
                    random.seed(d)
                    element_sub_item.text = str(random.getrandbits(29))
                    keys.append(d)
                elif header_row[ind] in reseed and d and header_row[ind].lower() in low_reseed:
                    random.seed(d)
                    element_sub_item.text = str(random.getrandbits(12))
                    keys.append(d)
            if "Brand" in os.path.basename(file_path) and '---'.join(keys) in brand_keys:
                main_top.remove(item)
            elif "PrgMst" in os.path.basename(file_path) and '---'.join(keys) in program_keys:
                main_top.remove(item)
            elif "PromoMst" in os.path.basename(file_path) and '---'.join(keys) in promo_keys:
                main_top.remove(item)
            elif "Genre" in os.path.basename(file_path) and '---'.join(keys) in genre_keys:
                main_top.remove(item)
            else:
                element_sub_item = ET.SubElement(item, "Id")
                element_sub_item.text = str(uuid.uuid4())

        brand_keys = set(brand_keys)
        promo_keys = set(promo_keys)
        program_keys = set(program_keys)
        genre_keys = set(genre_keys)

        # feeder_path = file_path.replace("source", "feeder2")
        # tmp_tmp = feeder_path + ".tmp"
        # subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, feeder_path])
        # subprocess.run(["mv", tmp_tmp, feeder_path])
        #
        # if "Brand" in os.path.basename(feeder_path):
        #     header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
        #                   "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
        #                   "Advertisinggroupcode",
        #                   "Descriptor", "Descriptorcode"]
        #     cdata_row = ["Brandname", "Title", "Brandsector",
        #                  "Brandcategory", "Advertiser", "Advertisinggroup",
        #                  "Descriptor"]
        # elif "PromoMst" in os.path.basename(feeder_path):
        #     header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
        #                   "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
        #                   "Advertisinggroupcode",
        #                   "Descriptor", "Descriptorcode"]
        #     cdata_row = ["Brandname", "Title", "Brandsector",
        #                  "Brandcategory", "Advertiser", "Advertisinggroup",
        #                  "Descriptor"]
        # elif "PrgMst" in os.path.basename(feeder_path):
        #     header_row = ["Channelnamecode", "Channelname", "Title", "Titlecode", "Contentlanguage",
        #                   "Contentlanguagecode",
        #                   "Programtheme", "Programthemecode", "Programgenre", "Programgenrecod", "Productionhouse",
        #                   "Prodhouse"]
        #     cdata_row = ["Channelname", "Title", "Contentlanguage",
        #                  "Programtheme", "Programgenre", "Productionhouse"]
        # # elif "ChnMst" in os.path.basename(file_path):
        # #     header_row = ["Channel", "Channelcode", "Networkname", "Networkcode", "Language", "Languagecode", "Region",
        # #                   "Regioncode", "Genre", "Genrecode"]
        # #     cdata_row = ["Channel", "Networkname", "Language", "Region", "Genre"]
        # # elif "PromoCategory" in os.path.basename(file_path):
        # #     header_row = ["PromoCategory", "PromoCategoryCode"]
        # #     cdata_row = ["PromoCategory"]
        # elif "Genre" in os.path.basename(file_path):
        #     header_row = ["PROGRAMGENRE", "PROGRAMGENRECODE", "PROGRAMTHEME", "PROGRAMTHEMECODE"]
        #     cdata_row = ["PROGRAMGENRE", "PROGRAMTHEME"]
        # # elif "Content" in os.path.basename(file_path):
        # #     header_row = ["CONTENTLANGUAGE", "CONTENTLANGUAGECODE"]
        # #     cdata_row = ["CONTENTLANGUAGE"]
        # else:
        #     indent(main_top)
        #     with open(output_path, 'wb') as xml_file:
        #         main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        #     continue
        # tree = ElementTree.parse(feeder_path)
        # root = tree.getroot()
        # data = []
        # for child in root:
        #     row_data = []
        #     for gc in child:
        #         row_data.append(gc.text)
        #     data.append(row_data)

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
                if header_row[ind] in reseed and d and header_row[ind].lower() not in low_reseed:
                    random.seed(d)
                    element_sub_item.text = str(random.getrandbits(29))
                    keys.append(d)
                elif header_row[ind] in reseed and d and header_row[ind].lower() in low_reseed:
                    random.seed(d)
                    element_sub_item.text = str(random.getrandbits(12))
                    keys.append(d)
            if "Brand" in os.path.basename(file_path) and '---'.join(keys) in brand_keys:
                main_top.remove(item)
            elif "PrgMst" in os.path.basename(file_path) and '---'.join(keys) in program_keys:
                main_top.remove(item)
            elif "PromoMst" in os.path.basename(file_path) and '---'.join(keys) in promo_keys:
                main_top.remove(item)
            elif "Genre" in os.path.basename(file_path) and '---'.join(keys) in genre_keys:
                main_top.remove(item)
            else:
                element_sub_item = ET.SubElement(item, "Id")
                element_sub_item.text = str(uuid.uuid4())
        indent(main_top)
        with open(output_path, 'wb') as xml_file:
            main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
