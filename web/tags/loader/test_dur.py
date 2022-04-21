from xml.etree import ElementTree
# from masters.models import Vendor, VendorCommercial
import glob, argparse
import math, os
import csv


def tcr2sec(tcr):

    h = int(tcr.split(":")[0])
    m = int(tcr.split(":")[1])
    s = int(tcr.split(":")[2])
    return int(h*3600+m*60+s)


def load(data, file='/tmp/Zee_TV_18-04-19.xml', vendor="TABSONS"):

    tree = ElementTree.parse(file)
    root = tree.getroot()
    ch = os.path.basename(file)[0:-12].replace("_"," ")
    print(ch)
    for child in root:
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        if row_data[1] == "Commercial":
            dur = str(tcr2sec(row_data[14]))
            if vendor in data:
                if row_data[7] in data[vendor]:
                    if row_data[15] in data[vendor][row_data[7]]:
                        durs = [f[1] for f in data[vendor][row_data[7]][row_data[15]]]
                        if dur not in durs:
                            data[vendor][row_data[7]][row_data[15]].append((ch,dur))
                    else:
                        data[vendor][row_data[7]][row_data[15]] = [(ch,dur)]
                else:
                    data[vendor][row_data[7]]={row_data[15]: [(ch,dur)]}
            else:
                data[vendor] = {row_data[7]: {row_data[15]: [(ch,dur)]}}

    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--folder')
    parser.add_argument('-v', '--vendor')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()
    data = {}
    for f in glob.glob(os.path.join(args.folder, '*.xml')):
        # print(f)
        data = load(data, f, args.vendor)
    with open(args.output, 'w+') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='"')

        for f in data:
            for dt in data[f]:
                for desc in data[f][dt]:
                    if len(data[f][dt][desc]) > 1:
                        tmp = [f, dt, desc]
                        for tg in data[f][dt][desc]:
                            tmp += tg
                        spamwriter.writerow(tmp)