import argparse
import glob
import os
import tqdm
from xml.etree import ElementTree
from lxml import etree as ET
import errno, random, subprocess


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


def convert(dir):


    reports = os.path.join(dir,'*.xml')
    header_row = ["Broadcastercode", "ContentType", "ContentTypeCode", "ChannelNameCode", "ChannelGenreCode",
                  "ChannelRegionCode", "ChannelLanguageCode", "Title", "TitleCode", "ContentLanguageCode",
                  "TelecastDate", "TelecastDay", "TelecastStartTime", "TelecastEndTime", "TelecastDuration",
                  "DescriptorCode", "BreakNumber", "PositionInBreak", "CountInBreak", "DurationInBreak",
                  "BreakDuration", "CountPerProgram", "DurationPerProgram", "TotalBreakCountPerProgram",
                  "TotalBreakDurationPerProgram", "PromoTypeCode", "PromoCategoryCode", "PromoChannelCode",
                  "PromoSponsorName", "PromoProgramNameCode", "PromoProgramThemeCode", "PromoProgramGenreCode",
                  "ProgramThemeCode", "ProgramGenreCode", "ProgramSegmentNumber", "NumberOfSegmentsInProgram",
                  "BrandSectorCode", "BrandCategoryCode", "ProductServiceNameCode", "BrandNameCode",
                  "SubBrandNameCode",
                  "AdvertiserCode", "AdvertisingGroupCode", "CommercialProgramNameCode",
                  "CommercialProgramThemeCode", "CommercialProgramGenreCode", "Sport", "OriginalOrRepeat",
                  "Live", "CombinedPositionInBreak", "CombinedCountInBreak", "PromoProgramStartTime",
                  "CommercialProgramStartTime", "SpotId", "LastModifiedDate", "AdBreakCode",
                  "PromoBroadcasterCode", "Beam", "Split", "Market", "SplitRegion", "SplitPlatform",
                  "ProdHouse"]
    cdata_row = ["Title",
                 "PromoSponsorName", "AdBreakCode", "Beam", "Split", "Market", "SplitRegion", "SplitPlatform",
                 "ProdHouse"]
    reseed = ["TitleCode", "DescriptorCode", "BrandNameCode", "BrandSectorCode", "BrandCategoryCode", "AdvertiserCode",
              "AdvertisingGroupCode", "CommercialProgramNameCode", "PromoProgramNameCode", "PromoTypeCode"]
    low_reseed = ["AdvertisingGroupCode"]
    for file_path in tqdm.tqdm(glob.glob(reports)):
        tmp_tmp = file_path + ".tmp"
        subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, file_path])
        subprocess.run(["mv", tmp_tmp, file_path])
        tree = ElementTree.parse(file_path)
        root = tree.getroot()
        data = []
        for child in root:
            row_data = []
            for gc in child:
                    row_data.append(gc.text)
            data.append(row_data)
        top = ET.Element("BarcPlayoutMonitoring")
        tree = ET.ElementTree(top)
        for row_ind, row_data in enumerate(data):
            item = ET.SubElement(top, 'Item')
            for ind, d in enumerate(row_data):
                element_sub_item = ET.SubElement(item, header_row[ind])
                if d:
                    element_sub_item.text = str(d)
                else:
                    element_sub_item.text = ''
                if header_row[ind] in cdata_row:
                    element_sub_item.text = ET.CDATA(element_sub_item.text)
                if header_row[ind] in reseed and d and header_row[ind] not in low_reseed:
                    # print(header_row[ind])
                    random.seed(d)
                    element_sub_item.text = str(random.getrandbits(29))
                    # print(str(random.getrandbits(29)))
                elif header_row[ind] in reseed and d and header_row[ind] in low_reseed:
                    # print(header_row[ind])
                    random.seed(d)
                    element_sub_item.text = str(random.getrandbits(12))
                    # print(random.getrandbits(12))
        output_path = os.path.join(dir, 'converted', os.path.basename(file_path))
        check_or_create_file(output_path)
        indent(top)
        with open(output_path, 'wb') as xml_file:
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
