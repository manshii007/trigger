import argparse
import glob
import os
import tqdm
from xml.etree import ElementTree
from lxml import etree as ET
import errno, random, subprocess
from shutil import copyfile
import uuid, json


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

    source_masters = os.path.join(args.dir, '*.xml')

    for file_path in tqdm.tqdm(glob.glob(source_masters)):
        brand_keys = []
        promo_keys = []
        program_keys = []
        genre_keys = []
        print(file_path)
        tmp_tmp = file_path + ".tmp"
        subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, file_path])
        subprocess.run(["mv", tmp_tmp, file_path])
        output_path = os.path.join(args.dir, 'converted', 'masterchanges', os.path.basename(file_path).split(".")[0]+".json")
        check_or_create_file(output_path)
        top_txt = ""

        tree = ElementTree.parse(file_path)
        root = tree.getroot()
        data = []
        for child in root:
            row_data = []
            for gc in child:
                row_data.append(gc.text)
            data.append(row_data)

        if "Brand" in os.path.basename(file_path):
            top_txt ="BarcBrandMaster"
            header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                          "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                          "Advertisinggroupcode",
                          "Descriptor", "Descriptorcode"]
            cdata_row = ["Brandname", "Title", "Brandsector",
                         "Brandcategory", "Advertiser", "Advertisinggroup",
                         "Descriptor"]
            with open(output_path, 'w', encoding='utf-8') as f:
                json_data = []
                for row_data in tqdm.tqdm(data):
                    tmp = {}
                    tmp['id'] = row_data[-1]
                    tmp['original_id'] = ''
                    tmp['brand_name'] = {
                        "name": row_data[0],
                        "code": row_data[1],
                        "original_code": "",
                        "brand_category": {
                            "name" : row_data[6],
                            "code": row_data[7],
                            "original_code": "",
                            "brand_sector": {
                                "name": row_data[4],
                                "code": row_data[5],
                                "original_code":""
                            }
                        }
                    }
                    tmp['advertiser'] = {
                        'name': row_data[8],
                        'code': row_data[9],
                        'original_code': "",
                        'advertiser_group': {
                            "name": row_data[10],
                            "code": row_data[11],
                            "original_code": ""
                        }
                    }
                    tmp['descriptor'] = {
                        'text': row_data[12],
                        "code": row_data[13],
                        "original_code": ""
                    }
                    tmp['status'] = 'new'
                    json_data.append(tmp)
                json.dump(json_data, f, indent=2)

        elif "PromoMst" in os.path.basename(file_path):
            top_txt ="BarcPromoMaster"
            header_row = ["Brandname", "Brandnamecode", "Title", "Titlecode", "Brandsector", "Brandsectorcode",
                          "Brandcategory", "Brandcategorycode", "Advertiser", "Advertisercode", "Advertisinggroup",
                          "Advertisinggroupcode",
                          "Descriptor", "Descriptorcode"]
            cdata_row = ["Brandname", "Title", "Brandsector",
                         "Brandcategory", "Advertiser", "Advertisinggroup",
                         "Descriptor"]
            with open(output_path, 'w', encoding='utf-8') as f:
                json_data = []
                for row_data in tqdm.tqdm(data):
                    tmp = {}
                    tmp['id'] = row_data[-1]
                    tmp['original_id'] = ''
                    tmp['brand_name'] = {
                        "name": row_data[0],
                        "code": row_data[1],
                        "original_code": "",
                        "brand_category": {
                            "name" : row_data[6],
                            "code": row_data[7],
                            "original_code": "",
                            "brand_sector": {
                                "name": row_data[4],
                                "code": row_data[5],
                                "original_code":""
                            }
                        }
                    }
                    tmp['advertiser'] = {
                        'name': row_data[8],
                        'code': row_data[9],
                        'original_code': "",
                        'advertiser_group': {
                            "name": row_data[10],
                            "code": row_data[11],
                            "original_code": ""
                        }
                    }
                    tmp['descriptor'] = {
                        'text': row_data[12],
                        "code": row_data[13],
                        "original_code": ""
                    }
                    tmp['status'] = 'new'
                    json_data.append(tmp)
                json.dump(json_data, f, indent=2)
        elif "PrgMst" in os.path.basename(file_path):
            top_txt ="BarcProgramMaster"
            header_row = ["Channelnamecode", "Channelname", "Title", "Titlecode", "Contentlanguage", "Contentlanguagecode",
                          "Programtheme", "Programthemecode", "Programgenre", "Programgenrecod", "Productionhouse",
                          "Prodhouse"]
            cdata_row = ["Channelname", "Title", "Contentlanguage",
                          "Programtheme", "Programgenre", "Productionhouse"]
            with open(output_path, 'w', encoding='utf-8') as f:
                json_data = []
                for row_data in tqdm.tqdm(data):
                    tmp = {}
                    tmp['id'] = row_data[-1]
                    tmp['original_id'] = ''
                    tmp['title'] = {
                        "name": row_data[2],
                        "code": row_data[3],
                        "original_code": "",
                    }
                    tmp['program_genre'] = {
                        'name': row_data[8],
                        'code': row_data[9],
                        'original_code': "",
                        'program_theme': {
                            "name": row_data[6],
                            "code": row_data[7],
                            "original_code": ""
                        }
                    }
                    tmp['prod_house'] = {
                        'name': row_data[10],
                        "code": row_data[11],
                        "original_code": ""
                    }
                    tmp['channel'] = {
                        'name': row_data[1],
                        "code": row_data[0],
                        "original_code": ""
                    }
                    tmp['language'] = {
                        'name': row_data[4],
                        "code": row_data[5],
                        "original_code": ""
                    }
                    tmp['status'] = 'new'
                    json_data.append(tmp)
                json.dump(json_data, f, indent=2)
        elif "ChnMst" in os.path.basename(file_path):
            top_txt="BarcChannelMaster"
            header_row = ["Channel", "Channelcode", "Networkname", "Networkcode", "Language", "Languagecode", "Region",
                          "Regioncode", "Genre", "Genrecode"]
            cdata_row = ["Channel", "Networkname", "Language", "Region", "Genre"]
            with open(output_path, 'w', encoding='utf-8') as f:
                json_data = []
                for row_data in tqdm.tqdm(data):
                    tmp = {}
                    tmp['id'] = row_data[-1]
                    tmp['original_id'] = ''
                    tmp['channel'] = {
                        "name": row_data[0],
                        "code": row_data[1],
                        "original_code": "",
                    }
                    tmp['network'] = {
                        'name': row_data[2],
                        'code': row_data[3],
                        'original_code': "",
                    }
                    tmp['region'] = {
                        'name': row_data[6],
                        "code": row_data[7],
                        "original_code": ""
                    }
                    tmp['language'] = {
                        'name': row_data[4],
                        "code": row_data[5],
                        "original_code": ""
                    }
                    tmp['genre'] = {
                        'name': row_data[8],
                        "code": row_data[9],
                        "original_code": ""
                    }
                    tmp['status'] = 'new'
                    json_data.append(tmp)
                json.dump(json_data, f, indent=2)
        elif "PromoCategory" in os.path.basename(file_path):
            top_txt="BarcPromoCategoryMaster"
            header_row = ["PromoCategory", "PromoCategoryCode"]
            cdata_row = ["PromoCategory"]
            with open(output_path, 'w', encoding='utf-8') as f:
                json_data = []
                for row_data in tqdm.tqdm(data):
                    tmp = {}
                    tmp['id'] = row_data[-1]
                    tmp['original_id'] = ''
                    tmp['original_code'] = ''
                    tmp['name'] = row_data[0]
                    tmp['code'] = row_data[1]
                    tmp['status'] = 'new'
                    json_data.append(tmp)
                json.dump(json_data, f, indent=2)
        elif "Genre" in os.path.basename(file_path): # pft different
            top_txt="GenreMaster"
            header_row = ["PROGRAMGENRECODE", "PROGRAMGENRE", "PROGRAMTHEMECODE", "PROGRAMTHEME"]
            cdata_row = ["PROGRAMGENRE", "PROGRAMTHEME"]
            with open(output_path, 'w', encoding='utf-8') as f:
                json_data = []
                for row_data in tqdm.tqdm(data):
                    tmp = {}
                    tmp['id'] = row_data[-1]
                    tmp['original_id'] = ''
                    tmp['original_code'] = ''
                    tmp['name'] = row_data[1]
                    tmp['code'] = row_data[0]
                    tmp['program_theme'] = {
                        'name': row_data[3],
                        'code': row_data[2],
                        'original_code': ''
                    }
                    tmp['status'] = 'new'
                    json_data.append(tmp)
                json.dump(json_data, f, indent=2)
        elif "Content" in os.path.basename(file_path): # pft different
            top_txt = "CURGEN"
            header_row = ["CONTENTLANGUAGECODE", "CONTENTLANGUAGE"]
            cdata_row = ["CONTENTLANGUAGE"]
            with open(output_path, 'w', encoding='utf-8') as f:
                json_data = []
                for row_data in tqdm.tqdm(data):
                    tmp = {}
                    tmp['id'] = row_data[-1]
                    tmp['original_id'] = ''
                    tmp['original_code'] = ''
                    tmp['name'] = row_data[1]
                    tmp['code'] = row_data[0]
                    tmp['status'] = 'new'
                    json_data.append(tmp)
                json.dump(json_data, f, indent=2)
