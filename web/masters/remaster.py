import argparse
import glob
import os
import tqdm
from xml.etree import ElementTree
from lxml import etree as ET
import errno, random, subprocess
from shutil import copyfile


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


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir')

    args = parser.parse_args()

    reports = os.path.join(args.dir, '*.xml')

    for file_path in tqdm.tqdm(glob.glob(reports)):
        tmp_tmp = file_path + ".tmp"
        subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, file_path])
        subprocess.run(["mv", tmp_tmp, file_path])
        output_path = os.path.join(args.dir, 'converted', 'masters', os.path.basename(file_path))
        check_or_create_file(output_path)
        top_txt = ""

        reseed = ["brandnamecode", "titlecode", "brandsectorcode", "brandcategorycode", "advertisercode",
                  "advertisinggroupcode",
                  "descriptorcode"]

        low_reseed = ["advertisinggroupcode"]

        if "Brand" in os.path.basename(file_path):
            top_txt = "BarcBrandMaster"
            header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                          "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                          "Advertisinggroupcode",
                          "Descriptor", "Descriptorcode"]
            cdata_row = ["Brandname", "Title", "Brandsector",
                         "Brandcategory", "Advertiser", "Advertisinggroup",
                         "Descriptor"]
        elif "PromoMst" in os.path.basename(file_path):
            top_txt = "BarcPromoMaster"
            header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                          "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                          "Advertisinggroupcode",
                          "Descriptor", "Descriptorcode"]
            cdata_row = ["Brandname", "Title", "Brandsector",
                         "Brandcategory", "Advertiser", "Advertisinggroup",
                         "Descriptor"]
        elif "PrgMst" in os.path.basename(file_path):
            top_txt = "BarcProgramMaster"
            header_row = ["Channelname", "Channelnamecode", "Title", "Titlecode", "Contentlanguage",
                          "Contentlanguagecode",
                          "Programtheme", "Programthemecode", "Programgenre", "Programgenrecod", "Productionhouse",
                          "Prodhouse"]
            cdata_row = ["Channelname", "Title", "Contentlanguage",
                         "Programtheme", "Programgenre", "Productionhouse"]
        elif "Genre" in os.path.basename(file_path):
            top_txt = "GenreMaster"
            header_row = ["PROGRAMGENRECODE", "PROGRAMGENRE", "PROGRAMTHEMECODE", "PROGRAMTHEME"]
            cdata_row = ["PROGRAMGENRE", "PROGRAMTHEME"]
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
            for ind, d in enumerate(row_data):
                element_sub_item = ET.SubElement(item, header_row[ind])
                if d:
                    element_sub_item.text = str(d)
                else:
                    element_sub_item.text = ''
                if header_row[ind] in cdata_row:
                    element_sub_item.text = ET.CDATA(element_sub_item.text)
                if header_row[ind].lower() in reseed and d and (header_row[ind].lower() not in low_reseed):
                    random.seed(d)
                    element_sub_item.text = str(random.getrandbits(29))
                elif header_row[ind].lower() in reseed and d and header_row[ind].lower() in low_reseed:
                    random.seed(d)
                    element_sub_item.text = str(random.getrandbits(12))

        indent(main_top)
        with open(output_path, 'wb') as xml_file:
            main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
