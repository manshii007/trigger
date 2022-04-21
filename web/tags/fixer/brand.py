import argparse
import os
import tqdm
from xml.etree import ElementTree
import errno, random


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


def load(file='./masters/data/TAM/BrandMstXml_20190416.xml', output_path=None):
    tree = ElementTree.parse(file)
    root = tree.getroot()
    data = []
    adgroupskeys = {}
    sectorskeys = {}
    deskeys = {}
    adskeys = {}
    catskeys = {}
    nameskeys = {}
    namecodes = set()
    adgroupcodes = set()
    descodes = set()
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        data.append(row_data)
        if row_data[11] not in adgroupskeys:
            adgroupskeys[row_data[11]] = {row_data[10]:row_data[11]}
            adgroupcodes.add(row_data[11])
        elif row_data[10] not in adgroupskeys[row_data[11]]:
            d = random.getrandbits(29)
            while d in adgroupcodes:
                d = random.getrandbits(29)
            adgroupskeys[row_data[11]][row_data[10]]=d
            adgroupcodes.add(d)

        if row_data[5] not in sectorskeys:
            sectorskeys[row_data[5]] = {row_data[4]:row_data[5]}
        elif row_data[4] not in sectorskeys[row_data[5]]:
            sectorskeys[row_data[5]][row_data[4]]=random.getrandbits(29)

        if row_data[13] not in deskeys:
            deskeys[row_data[13]] = {row_data[12]:row_data[13]}
            descodes.add(row_data[13])
        elif row_data[12] not in deskeys[row_data[13]]:
            d = random.getrandbits(29)
            while d in adgroupcodes:
                d = random.getrandbits(29)
            deskeys[row_data[13]][row_data[12]]=d
            descodes.add(d)

        if row_data[9] not in adskeys:
            adskeys[row_data[9]] = {row_data[8]:row_data[9]}
        elif row_data[8] not in adskeys[row_data[9]]:
            adskeys[row_data[9]][row_data[8]]=random.getrandbits(29)

        if row_data[7] not in catskeys:
            catskeys[row_data[7]] = {row_data[6]:row_data[7]}
        elif row_data[6] not in catskeys[row_data[7]]:
            catskeys[row_data[7]][row_data[6]]=random.getrandbits(29)

        if row_data[1] not in nameskeys:
            d = row_data[1]
            while d in namecodes:
                d = random.getrandbits(32)
            nameskeys[row_data[1]] = {row_data[0]:d}
            namecodes.add(d)
        elif row_data[0] not in nameskeys[row_data[1]]:
            d = random.getrandbits(32)
            while d in namecodes:
                d = random.getrandbits(32)
            nameskeys[row_data[1]][row_data[0]]=d
            namecodes.add(d)

    header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                  "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                  "Advertisinggroupcode",
                  "Descriptor", "Descriptorcode", "Id"]
    reseed = ["Brandnamecode", "Titlecode", "Brandsectorcode", "Brandcategorycode", "Advertisercode",
              "Advertisinggroupcode",
              "Descriptorcode"]
    top_txt = "BarcBrandMaster"
    main_top = ElementTree.Element(top_txt)
    main_tree = ElementTree.ElementTree(main_top)
    for row_data in tqdm.tqdm(data):
        item = ElementTree.SubElement(main_top, 'Item')
        for ind, d in enumerate(row_data):
            element_sub_item = ElementTree.SubElement(item, header_row[ind])
            if d and header_row[ind] not in reseed:
                element_sub_item.text = str(d)
            elif header_row[ind] == "Brandnamecode":
                c = nameskeys[d][row_data[ind-1]]
                element_sub_item.text = str(c)
            elif header_row[ind] == "Titlecode":
                c = nameskeys[d][row_data[ind-1]]
                element_sub_item.text = str(c)
            elif header_row[ind] == "Brandsectorcode":
                c = sectorskeys[d][row_data[ind-1]]
                element_sub_item.text = str(c)
            elif header_row[ind] == "Brandcategorycode":
                c = catskeys[d][row_data[ind-1]]
                element_sub_item.text = str(c)
            elif header_row[ind] == "Advertisercode":
                c = adskeys[d][row_data[ind-1]]
                element_sub_item.text = str(c)
            elif header_row[ind] == "Advertisinggroupcode":
                c = adgroupskeys[d][row_data[ind-1]]
                element_sub_item.text = str(c)
            elif header_row[ind] == "Descriptorcode":
                c = deskeys[d][row_data[ind-1]]
                element_sub_item.text = str(c)
            else:
                element_sub_item.text = ''
    indent(main_top)
    with open(output_path, 'wb') as xml_file:
        main_tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    print("------------------------------Done----------------------------------")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir')
    parser.add_argument('-f', '--file')
    parser.add_argument('-o', '--out')
    args = parser.parse_args()

    load(args.file, args.out)