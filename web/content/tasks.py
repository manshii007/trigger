
from __future__ import absolute_import, unicode_literals
from celery import Celery
import calendar
import logging, os, errno, uuid
from .models import PersonGroup, CloudPerson, ChannelClip, Channel, Song, Genre, Movie, Person, Label
from contextual.models import Face
import cognitive_face as CF
from billiard.pool import MaybeEncodingError
import boto3
from django.core.mail import send_mail, EmailMessage
from .fingerprint import fingerprint
import math, subprocess, requests, io, shutil
from datetime import datetime, timedelta
from datetime import date as date_lib
import csv
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.exceptions import MultipleObjectsReturned
import random
from random import randint
from .constants import channel_abr, channel_brf

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
from django.http import HttpResponse
from django.contrib.contenttypes.models import ContentType
from video.tasks import sec2tcr
# from xml.etree import ElementTree
from urllib.request import urlretrieve
from tags.models import Fingerprint, PlayoutTag, ProgramGenre, Program, Promo, Commercial, Title, Descriptor, BrandName, BrandSector, BrandCategory, ProgramTheme
from tags.models import Channel as SpecChannel



KEY = 'e80b3b4c298043f8aa6fca9a6e5f343c'  # Replace with a valid subscription key (keeping the quotes in place).
CF.Key.set(KEY)

s3_client = boto3.client('s3')

app = Celery('content')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

logger = logging.getLogger('debug')


@app.task
def create_folder(asset_name, bucket_path="viacom-pilot-content", emails="aswin@tessact.com,ashok.salian@viacom18.com"):
    f_path = '{}/tmp.txt'.format(asset_name)
    s3_client.put_object(Body=b'', Bucket=bucket_path, Key=f_path)
    # initiate a mail
    recipients = emails.split(',')
    recipients_set = set(recipients)
    recipients_list = list(recipients_set)
    email = EmailMessage(
        'Asset Created for {}'.format(asset_name, ),
        'Folder Path : s3:{}/{}'.format(bucket_path, asset_name),
        'aswin@tessact.com',
        recipients_list
    )
    email.send()

    return True


@app.task
def upload_to_azure_cloud(groupIds):
    for personGroupId in groupIds:
        personGroup = PersonGroup.objects.get(id=personGroupId)
        personGroup.upload_progress = 0
        personGroup.save()
        try:
            CF.person_group.create(str(personGroup.id), user_data=personGroup.title)
        except CF.CognitiveFaceException:
            pass
        persons = CF.person.lists(str(personGroup.id))
        person_hash = {}
        for person in persons:
            person_hash[person['name']] = person['personId']
            CF.person.delete(str(personGroupId), person['personId'])
        count = 0
        for person in personGroup.persons.all():

            personGroup.upload_progress = count/len(personGroup.persons.all())
            personGroup.save()
            count += 1
            logger.debug(person.name)
            info = CF.person.create(str(personGroup.id), person.name)
            person_id = info['personId']
            faces = Face.objects.filter(face_group__person=person).filter(selected=True)
            for face in faces:
                try:
                    CF.person.add_face(face.face_img_url, str(personGroup.id), person_id)
                except CF.CognitiveFaceException:
                    pass
                except MaybeEncodingError:
                    pass
            CloudPerson.objects.filter(person=person).delete()
            cloudPerson = CloudPerson.objects.get_or_create(person=person, cloud_id=person_id)
        personGroup.upload_progress = 1
        personGroup.save()
        personGroup.start_training()


def check_or_create_file(file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occurred


def generate_matches(ad, main):
    print(max(ad.keys()), max(main.keys()))
    hits = []
    hit_map = [0]*(max(main.keys())+1)
    ln = len(ad.keys())
    for i in main:
        start = 0
        fails = 0
        for j in sorted(ad.keys()):
            if i+j in main:
                ad_freq_map = ad[j]
                freq_map = main[i+j]
                if sum([t in freq_map for t in ad_freq_map]) > 2:
                    # print("Hit at {} {}".format(j,i))
                    hits.append((j,i))
                    try:
                        if not start:
                            start=j

                        hit_map[i] = j - start
                        fails = 0
                    except IndexError:
                        print(i, j)
                else:
                    fails +=1
            else:
                fails+=1

            if fails>ln/5:
                hit_map[i] = 0
                break
    return hit_map


def str_2_int_dict(d):
    tmp = {}
    for i in d.keys():
        tmp[int(i)] = []
        for k in d[i]:
            tmp[int(i)].append(int(k))
    return tmp


@app.task
def get_fingerprint(channel_clip_id):
    vid = ChannelClip.objects.filter(id= channel_clip_id).first()
    if vid:
        # create fingerprints for teams
        print("cutting and analyzing video")
        video_url = vid.video.file
        audio_url = video_url.replace(".mp4", ".aac")
        tmp_file_name = os.path.join('/tmp/audio/', str(uuid.uuid4()) + '.aac')
        print(tmp_file_name)
        check_or_create_file(tmp_file_name)
        urlretrieve(audio_url, tmp_file_name)
        tr = fingerprint(tmp_file_name)
        silentremove(tmp_file_name)
        fg = Fingerprint.objects.create(video=vid.video, fprint=tr)
        fg.save()
        # frequency map
        # tr = str_2_int_dict(tr)
        # fr_map = {}
        # for i in tr.keys():
        #     for f in tr[i]:
        #         if f in fr_map:
        #             if i not in fr_map[f]:
        #                 fr_map[f].append(i)
        #         else:
        #             fr_map[f] = [i]
        # # get all commercial from today
        # border_date = vid.date - timedelta(days=7)
        # end_date = vid.date - timedelta(days=2)
        # pt = PlayoutTag.objects.filter(video__channelclip__date__gte=border_date, video__channelclip__date__lt=end_date)
        # c_tags = pt.filter(content_type='commercial').values('object_id').distinct()
        # for c_tag in c_tags:
        #     ptag = pt.filter(object_id=c_tag['object_id']).first()
        #     main_fp = Fingerprint.objects.filter(video=ptag.video).first()
        #     if main_fp:
        #         start = ptag.frame_in / 25
        #         end = ptag.frame_out / 25
        #         c_freq_map = {}
        #         if start and end and main_fp:
        #             main_freq_map = main_fp.fprint
        #             main_freq_map = str_2_int_dict(main_freq_map)
        #             for i in main_freq_map:
        #                 if start * 96 <= i <= end * 96:
        #                     c_freq_map[i - start * 96] = main_freq_map[i]
        #             hit_map = generate_matches(c_freq_map, tr)
        #             m = max(c_freq_map.keys())
        #             hits = []
        #             for v in range(len(hit_map)):
        #                 if hit_map[v] > int(0.90 * m) and abs(int(v / 96) - start) > 9:
        #                     print(sec2tcr(int(v / 96)), hit_map[v] / m)
        #                     if int(v / 96) not in hits:
        #                         hits.append(int(v / 96))
        #                         p_tag, c = PlayoutTag.objects.get_or_create(video=vid.video, frame_in=math.ceil(v / 96) * 25,
        #                                                                     frame_out=(math.ceil(v / 96) + math.ceil(
        #                                                                         hit_map[v] / 96)) * 25,
        #                                                                     content_type=ptag.content_type,
        #                                                                     object_id=ptag.object_id,
        #                                                                     object_content_type=ptag.object_content_type,
        #                                                                     is_original=False)
        #                         if c:
        #                             print("Playout tag Created")


@app.task
def get_tag_fprints(tag_id):
    ptag = PlayoutTag.objects.filter(id=tag_id).first()
    dur = (ptag.frame_out - ptag.frame_in)/25
    if ptag and (ptag.content_type=="commercial" or ptag.content_type=="promo") and dur<30:
        cclip_tag = ChannelClip.objects.filter(video=ptag.video).first()
        if cclip_tag:
            fg = Fingerprint.objects.get(video=cclip_tag.video)
            trt = fg.fprint
            main_freq_map = str_2_int_dict(trt)
            if main_freq_map:
                start = (ptag.frame_in / 25) - 1
                end = (ptag.frame_out / 25)
                c_freq_map = {}
                if start and end and main_freq_map:
                    for i in main_freq_map:
                        if start * 96 <= int(i) <= end * 96:
                            c_freq_map[(int(i) - start * 96)] = main_freq_map[i]

                    dt = cclip_tag.date.__str__()
                    yy = int(dt.split("-")[0])
                    mm = int(dt.split("-")[1])
                    dd = int(dt.split("-")[2])

                    end_datetime = datetime(year=yy, month=mm, day=dd) + timedelta(hours=26)
                    c_clips = ChannelClip.objects.filter(channel=cclip_tag.channel, start_time__gt=cclip_tag.start_time, end_time__lt=end_datetime)

                    for c_clip in c_clips:
                        tr_fp = Fingerprint.objects.filter(video=c_clip.video).first()
                        tr = str_2_int_dict(tr_fp.fprint)
                        hit_map = generate_matches(c_freq_map, tr)
                        m = max(c_freq_map.keys())
                        hits = []
                        for v in range(len(hit_map)):
                            if hit_map[v] > int(0.9 * m) and abs(int(v / 96) - start) > 10:
                                print(sec2tcr(int(v / 96)), hit_map[v] / m)
                                if int(v / 96) not in hits:
                                    hits.append(int(v / 96))
                                    p_tag, c = PlayoutTag.objects.get_or_create(video=c_clip.video,
                                                                                frame_in=math.ceil(v / 96) * 25,
                                                                                frame_out=math.ceil(
                                                                                    v / 96) * 25 + ptag.frame_out - ptag.frame_in,
                                                                                content_type=ptag.content_type,
                                                                                object_id=ptag.object_id,
                                                                                object_content_type=ptag.object_content_type,
                                                                                is_original=False)


@app.task
def put_fingerprint(channel_clip_id):
    vid = ChannelClip.objects.filter(id= channel_clip_id).first()
    if vid:
        # create fingerprints for teams
        fg = Fingerprint.objects.get(video=vid.video)
        trt = fg.fprint
        tr = str_2_int_dict(trt)
        # frequency map
        fr_map = {}
        for i in tr.keys():
            for f in tr[i]:
                if f in fr_map:
                    if i not in fr_map[f]:
                        fr_map[f].append(i)
                else:
                    fr_map[f] = [i]
        # get all commercial from today
        # border_date = vid.date - timedelta(days=7)
        dt = vid.date.__str__()
        yy = int(dt.split("-")[0])
        mm = int(dt.split("-")[1])
        dd = int(dt.split("-")[2])
        start_datetime = datetime(year=yy, month=mm, day=13) + timedelta(hours=2)
        pt = PlayoutTag.objects.filter(video__channelclip__start_time__gte=start_datetime, video__channelclip__start_time__lt=vid.start_time, video__channelclip__channel__channel_code=vid.channel.channel_code)
        c_tags = pt.filter(content_type='promo').values('object_id').distinct()
        for c_tag in c_tags:
            ptag = pt.filter(object_id=c_tag['object_id']).first()

            if ptag:
                tagged_object = ptag.tagged_object
                if tagged_object.brand_name.name[0:2] == "TP":
                    main_fp = Fingerprint.objects.filter(video=ptag.video).first()
                    if main_fp:
                        start = (ptag.frame_in / 25) - 1
                        end = (ptag.frame_in / 25) + 2
                        c_freq_map = {}
                        if start and end and main_fp:
                            main_freq_mapt = main_fp.fprint
                            main_freq_map = str_2_int_dict(main_freq_mapt)
                            for i in main_freq_map:
                                if start * 96 <= int(i) <= end * 96:
                                    c_freq_map[(int(i) - start * 96)] = main_freq_map[i]
                            hit_map = generate_matches(c_freq_map, tr)
                            m = max(c_freq_map.keys())
                            hits = []
                            for v in range(len(hit_map)):
                                if hit_map[v] > int(0.95 * m):
                                    print(sec2tcr(int(v / 96)), hit_map[v] / m)
                                    if int(v / 96) not in hits:
                                        hits.append(int(v / 96))
                                        print(ptag)
                                        p_tag, c = PlayoutTag.objects.get_or_create(video=vid.video, frame_in=math.ceil(v / 96) * 25,
                                                                                    frame_out=math.ceil(v / 96) * 25 + ptag.frame_out - ptag.frame_in,
                                                                                    content_type=ptag.content_type,
                                                                                    object_id=ptag.object_id,
                                                                                    object_content_type=ptag.object_content_type,
                                                                                    is_original=False)
                else:
                    main_fp = Fingerprint.objects.filter(video=ptag.video).first()
                    if main_fp:
                        start = (ptag.frame_in / 25) - 1
                        end = (ptag.frame_in / 25)
                        c_freq_map = {}
                        if start and end and main_fp:
                            main_freq_mapt = main_fp.fprint
                            main_freq_map = str_2_int_dict(main_freq_mapt)
                            for i in main_freq_map:
                                if start * 96 <= int(i) <= end * 96:
                                    c_freq_map[(int(i) - start * 96)] = main_freq_map[i]
                            hit_map = generate_matches(c_freq_map, tr)
                            m = max(c_freq_map.keys())
                            hits = []
                            for v in range(len(hit_map)):
                                if hit_map[v] > int(0.90 * m) and abs(int(v / 96) - start) > 10:
                                    print(sec2tcr(int(v / 96)), hit_map[v] / m)
                                    if int(v / 96) not in hits:
                                        hits.append(int(v / 96))
                                        print(ptag)
                                        p_tag, c = PlayoutTag.objects.get_or_create(video=vid.video,
                                                                                    frame_in=math.ceil(v / 96) * 25,
                                                                                    frame_out=math.ceil(
                                                                                        v / 96) * 25 + ptag.frame_out - ptag.frame_in,
                                                                                    content_type=ptag.content_type,
                                                                                    object_id=ptag.object_id,
                                                                                    object_content_type=ptag.object_content_type,
                                                                                    is_original=False)

        c_tags = pt.filter(content_type='commercial').values('object_id').distinct()
        for c_tag in c_tags:
            ptag = pt.filter(object_id=c_tag['object_id']).first()
            if ptag:
                main_fp = Fingerprint.objects.filter(video=ptag.video).first()
                if main_fp:
                    start = (ptag.frame_in / 25) - 1
                    end = (ptag.frame_out / 25)
                    c_freq_map = {}
                    if start and end and main_fp:
                        main_freq_mapt = main_fp.fprint
                        main_freq_map = str_2_int_dict(main_freq_mapt)
                        for i in main_freq_map:
                            if start * 96 <= int(i) <= end * 96:
                                c_freq_map[(int(i) - start * 96)] = main_freq_map[i]
                        hit_map = generate_matches(c_freq_map, tr)
                        m = max(c_freq_map.keys())
                        hits = []
                        for v in range(len(hit_map)):
                            if hit_map[v] > int(0.9 * m) and abs(int(v / 96) - start) > 10:
                                print(sec2tcr(int(v / 96)), hit_map[v] / m)
                                if int(v / 96) not in hits:
                                    hits.append(int(v / 96))
                                    print(ptag.tagged_object.brand_name.name)
                                    p_tag, c = PlayoutTag.objects.get_or_create(video=vid.video,
                                                                                frame_in = math.ceil(v / 96) * 25,
                                                                                frame_out = math.ceil(v / 96) * 25 + ptag.frame_out - ptag.frame_in,
                                                                                content_type=ptag.content_type,
                                                                                object_id=ptag.object_id,
                                                                                object_content_type=ptag.object_content_type,
                                                                                is_original=False)


def reset_xml_child(obj_arr, value):
    for obj in obj_arr:
        obj.text = value


def reset_csv_row(data_rows, obj_ind, val_ind, value):
    for ind in obj_ind:
        tmp = data_rows[ind]
        tmp[val_ind] = value
        data_rows[ind] = tmp
    return data_rows


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
def send_report(channel_id, date, user_mail, ext):
    channel = Channel.objects.filter(id=channel_id).first()
    spec_channel = SpecChannel.objects.filter(code=channel.channel_code).first()
    # channel_clips = ChannelClip.objects.filter(channel=channel, date=date).order_by('start_time')
    yr = int(date.split('-')[0])
    mm = int(date.split('-')[1])
    dd = int(date.split('-')[2])
    start_datetime = datetime(year=yr, month=mm, day=dd) + timedelta(hours=2)
    end_datetime = datetime(year=yr, month=mm, day=dd) + timedelta(hours=26)
    channel_clips = ChannelClip.objects.filter(channel__id=channel_id, start_time__gte=start_datetime, end_time__lt=end_datetime).order_by('date', 'start_time')

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
    cdata_row = [ "Title",
                  "PromoSponsorName", "AdBreakCode", "Beam", "Split", "Market", "SplitRegion", "SplitPlatform",
                  "ProdHouse"]
    object_rows = [header_row]
    anchor_program = None
    anchor_clip = None
    anchor_tag = None
    break_count = 0
    break_per_program = 0
    break_duration = 0
    spot_count = 0
    spot_per_program = 0
    prev_tag = None
    prev_obj = None
    segment_count = 0
    count_in_break_child_arr = []
    break_duration_child_arr = []
    count_per_program_child_arr = []
    total_break_cont_per_program_child_arr = []
    total_break_duration_per_program_child_arr = []
    combined_count_per_break_child_arr = []
    position_in_break = 0
    number_of_segments_in_program_arr = []

    ind = 0
    tp_tag = False
    for c in channel_clips:
        btags = PlayoutTag.objects.filter(video=c.video).order_by("frame_in")
        clip_wise_count = 0
        for btag in btags:
            clip_wise_count += 1
            ind += 1
            obj = btag.tagged_object
            if obj is None:
                ind -= 1
                continue
            start_time = int(btag.frame_in / 25) - 1 if int(btag.frame_in / 25) ==1 else int(btag.frame_in / 25)
            end_time = int(btag.frame_out / 25)
            telecast_start_time = (c.start_time + timedelta(seconds=start_time)).strftime("%H:%M:%S")
            telecast_end_time = (c.start_time + timedelta(seconds=end_time)).strftime("%H:%M:%S")
            telecast_duration = sec2tcr(end_time - start_time + 1)

            if not (btag.content_type == "promo" and obj and obj.__str__()[0:2]=="TP"):
                tp_tag = False

            if btag.content_type == "program" and obj != anchor_program:
                reset_csv_row(object_rows, count_per_program_child_arr, header_row.index('CountPerProgram'),
                              str(spot_per_program))
                count_per_program_child_arr = []
                spot_per_program = 0
                reset_csv_row(object_rows, total_break_cont_per_program_child_arr,
                              header_row.index('TotalBreakCountPerProgram'), str(break_per_program))
                total_break_cont_per_program_child_arr = []
                # reset break when a new program hits the list
                break_per_program = 0
                reset_csv_row(object_rows, number_of_segments_in_program_arr,
                              header_row.index('NumberOfSegmentsInProgram'), str(segment_count))
                number_of_segments_in_program_arr = []
                segment_count = 1
                anchor_program = obj
                anchor_clip = c
                anchor_tag = btag
            elif obj == anchor_program and prev_tag != btag:
                segment_count += 1
            elif prev_tag == btag:
                ind-=1
                continue
            elif prev_obj and obj and  prev_obj == obj and clip_wise_count==1:
                object_rows[-1][header_row.index("TelecastEndTime")] = telecast_end_time
                ind-=1
                continue

            if prev_tag and prev_tag.content_type != "program" and btag.content_type == "program":
                reset_csv_row(object_rows, combined_count_per_break_child_arr, header_row.index('CombinedCountInBreak'),
                              str(position_in_break))
                reset_csv_row(object_rows, break_duration_child_arr, header_row.index('BreakDuration'),
                              sec2tcr(break_duration))
            if btag.content_type == "promo" or btag.content_type == "commercial":
                if prev_tag and prev_tag.content_type == "program":
                    break_count += 1
                    break_per_program += 1
                    break_duration = (end_time - start_time + 1)
                    spot_per_program += 1
                    position_in_break = 1
                    # reset the break child count here
                    reset_csv_row(object_rows, count_in_break_child_arr, header_row.index('CountInBreak'),
                                  str(spot_count))
                    count_in_break_child_arr = []
                    spot_count = 1
                    # reset the break duration here
                    break_duration_child_arr = []

                    if btag.content_type == "promo" and obj and obj.__str__()[0:2]=="TP":
                        if tp_tag:
                            print(obj.__str__())
                            ind -= 1
                            row_data = object_rows[-1]
                            row_data[header_row.index("TelecastEndTime")] = telecast_end_time
                            row_data[header_row.index("TelecastDuration")] = telecast_duration
                            row_data[header_row.index("PromoSponsorName")] += ",[{}|{}]".format(
                                obj.__str__().replace("TP ", ""), telecast_duration)
                            object_rows[-1] = row_data
                            continue
                        else:
                            tp_tag = True
                            spot_count += 1
                            spot_per_program += 1
                            position_in_break += 1
                            row_data = object_rows[-1].copy()
                            row_data[header_row.index("Title")] = "Sponsorship promo - " + row_data[
                                header_row.index("Title")]
                            row_data[header_row.index("PositionInBreak")] = str(position_in_break)
                            row_data[header_row.index("CombinedPositionInBreak")] = str(position_in_break)
                            row_data[header_row.index("TelecastStartTime")] = telecast_start_time
                            row_data[header_row.index("TelecastEndTime")] = telecast_end_time
                            row_data[header_row.index("TelecastDuration")] = telecast_duration
                            row_data[header_row.index("PromoTypeCode")] = "543"
                            row_data[header_row.index("PromoSponsorName")] = "[{}|{}]".format(
                                obj.__str__().replace("TP ", ""), telecast_duration)
                            combined_count_per_break_child_arr.append(ind)
                            count_in_break_child_arr.append(ind)
                            object_rows.append(row_data)
                            continue
                elif btag.content_type == "promo" and obj and obj.__str__()[0:2]=="TP":
                    # we have a tp tag
                    if tp_tag:
                        # print(obj.__str__())
                        ind -= 1
                        row_data = object_rows[-1]
                        row_data[header_row.index("TelecastEndTime")] = telecast_end_time
                        row_data[header_row.index("TelecastDuration")] = telecast_duration
                        row_data[header_row.index("PromoSponsorName")] += ",[{}|{}]".format(
                            obj.__str__().replace("TP ", ""), telecast_duration)
                        object_rows[-1] = row_data
                        continue
                    else:
                        tp_tag = True
                        spot_count += 1
                        spot_per_program += 1
                        position_in_break += 1
                        row_data = object_rows[-1].copy()
                        row_data[header_row.index("Title")] = "Sponsorship promo - " + row_data[header_row.index("Title")]
                        row_data[header_row.index("PositionInBreak")] = str(position_in_break)
                        row_data[header_row.index("CombinedPositionInBreak")] = str(position_in_break)
                        row_data[header_row.index("TelecastStartTime")]=telecast_start_time
                        row_data[header_row.index("TelecastEndTime")]=telecast_end_time
                        row_data[header_row.index("TelecastDuration")]=telecast_duration
                        row_data[header_row.index("PromoTypeCode")] = "543"
                        row_data[header_row.index("PromoSponsorName")] = "[{}|{}]".format(obj.__str__().replace("TP ",""),telecast_duration)
                        combined_count_per_break_child_arr.append(ind)
                        count_in_break_child_arr.append(ind)
                        object_rows.append(row_data)
                        continue
                else:
                    spot_count += 1
                    spot_per_program += 1
                    position_in_break += 1
                    break_duration += (end_time - start_time + 1)

            promo_channel = None
            if btag.content_type == "promo":
                tr_mat = [x in obj.__str__().split(" ") for x in channel_abr]
                if any(tr_mat):
                    promo_channel = SpecChannel.objects.filter(name__iexact=channel_brf[tr_mat.index(True)]).first()
                else:
                    if obj and obj.brand_name and obj.brand_name.brand_category and obj.brand_name.brand_category.code == 1123:
                        promo_channel = spec_channel
                # else:
                #     tr_mat = [x in obj.__str__() for x in channel_brf]
                #     if any(tr_mat):
                #         promo_channel = SpecChannel.objects.filter(name=channel_brf[tr_mat.index(True)]).first()
            # anchor start time
            anchor_start_time = int(anchor_tag.frame_in / 25) if anchor_tag is not None else None
            anchor_telecast_start_time = (anchor_clip.start_time + timedelta(seconds=anchor_start_time)).strftime(
                "%H:%M:%S") if anchor_tag is not None else None
            row_data = []
            # boardcaster code
            sc = SpecChannel.objects.filter(code=channel.channel_code).first()
            row_data.append("" if not sc or sc is None or sc.network is None else sc.network.code)
            # content_type
            row_data.append(btag.content_type)
            # content type code

            if btag.content_type == 'program':
                row_data.append('101')
            elif btag.content_type == 'promo':
                row_data.append('102')
            else:
                row_data.append('103')
            # channel name code
            row_data.append(str(channel.channel_code))
            # channel genre code
            row_data.append(str(spec_channel.genre.code))
            # channel region code
            row_data.append(str(spec_channel.region.code))
            # channel language code
            row_data.append(str(spec_channel.language.code))
            # title
            row_data.append(obj.__str__())
            # title code
            if btag.content_type != "promo":
                row_data.append('' if not obj.title else str(obj.title.code))
            else:
                row_data.append('' if obj is None or obj.brand_name is None else str(obj.brand_name.code))
            # content language code
            row_data.append(
                str(spec_channel.language.code) if btag.content_type != "program" or obj.language is None else str(
                    obj.language.code))
            # telecast date
            dt = c.date.__str__()
            yy = dt.split("-")[0]
            mm = dt.split("-")[1]
            dd = dt.split("-")[2]
            row_data.append("{}/{}/{}".format(dd, mm, yy))
            # telecast day
            row_data.append(list(calendar.day_name)[c.date.weekday()])
            # telecast_start_time
            row_data.append(str(telecast_start_time))
            # telecast_end_time
            row_data.append(str(telecast_end_time))
            # telecast_duration
            row_data.append(str(telecast_duration))
            # descriptor code
            if btag.content_type == "program" or obj.descriptor is None:
                row_data.append("")
            else:
                row_data.append(str(obj.descriptor.code))
            # break number
            row_data.append(str(break_count) if btag.content_type != "program" else '0')
            # position in break
            row_data.append(str(spot_count) if btag.content_type != "program" else '0')
            # count in break
            if btag.content_type != "program":
                row_data.append(str(spot_count))
                count_in_break_child_arr.append(ind)
            else:
                row_data.append('0')
            # duration in break
            if btag.content_type != "program":
                row_data.append(str(telecast_duration))
            else:
                row_data.append('')
            # break duration
            row_data.append('')
            if btag.content_type != "program":
                break_duration_child_arr.append(ind)
            # count per program
            row_data.append('0')
            if btag.content_type != "program":
                count_per_program_child_arr.append(ind)
            # duration per program
            row_data.append('')
            # total break count per program
            row_data.append('')
            if btag.content_type != "program":
                total_break_cont_per_program_child_arr.append(ind)
            # total break duration per program
            row_data.append('')
            if btag.content_type != "program":
                total_break_duration_per_program_child_arr.append(ind)
            # promo type code
            if btag.content_type == "commercial":
                row_data.append("0")
            else:
                row_data.append(
                    '' if btag.content_type != "promo" or obj.brand_name is None or obj.brand_name.brand_category is None else str(
                        obj.brand_name.brand_category.code))
            # promo category code
            if btag.content_type != "promo" or promo_channel is None or spec_channel is None:
                row_data.append("")
            else:
                if promo_channel == spec_channel:
                    row_data.append("20201")
                else:
                    row_data.append("20202")
            # promo channel code
            row_data.append('' if btag.content_type != "promo" or promo_channel is None else promo_channel.code)
            # promo sponsor name
            row_data.append('')
            # promo program name code
            row_data.append('' if (btag.content_type != "promo" or anchor_program is None) else str(
                anchor_program.title.code))
            # promo program theme code
            row_data.append('' if (
                    btag.content_type != "promo" or anchor_program is None or anchor_program.program_genre is None or anchor_program.program_genre.program_theme is None) else str(
                anchor_program.program_genre.program_theme.code))
            # promo program genre code
            row_data.append('' if (
                    btag.content_type != "promo" or anchor_program is None or anchor_program.program_genre is None) else str(
                anchor_program.program_genre.code))
            # program theme code
            row_data.append(
                '' if btag.content_type != "program" or obj.program_genre is None or obj.program_genre.program_theme is None else str(
                    obj.program_genre.program_theme.code))
            # program genre code
            row_data.append(
                '' if btag.content_type != "program" or obj.program_genre is None else str(obj.program_genre.code))
            # program segment number
            if btag.content_type == "promo" or btag.content_type == "commercial":
                row_data.append('0')
            else:
                row_data.append('' if btag.content_type != "program" else str(segment_count))
            # number of segments in program
            if btag.content_type == "program":
                row_data.append('')
                number_of_segments_in_program_arr.append(ind)
            elif btag.content_type == "promo" or btag.content_type == "commercial":
                row_data.append('0')
            else:
                row_data.append('')
            # brand sector code
            if btag.content_type == "promo":
                row_data.append('')
            else:
                row_data.append(
                    '' if btag.content_type == "program" or obj.brand_name is None or obj.brand_name.brand_category is None else str(
                        obj.brand_name.brand_category.brand_sector.code))
            # brand category code
            if btag.content_type == "promo":
                row_data.append('0')
            else:
                row_data.append(
                    '' if btag.content_type == "program" or obj.brand_name is None or obj.brand_name.brand_category is None else str(
                        obj.brand_name.brand_category.code))
            # product service name code
            row_data.append('')
            # brand name code
            row_data.append(
                '' if btag.content_type == "program" or obj.brand_name is None else str(obj.brand_name.code))
            # sub brand name code
            row_data.append('')
            # advertiser code
            if btag.content_type == "promo":
                row_data.append('0')
            else:
                row_data.append(
                    '' if btag.content_type == "program" or obj.advertiser is None else str(obj.advertiser.code))
            # advertiser group code
            if btag.content_type == "promo":
                row_data.append('0')
            else:
                row_data.append(
                    '' if btag.content_type == "program" or obj.advertiser is None or obj.advertiser.advertiser_group is None else str(
                        obj.advertiser.advertiser_group.code))
            # commercial program name  code
            row_data.append('' if (btag.content_type != "commercial" or anchor_program is None) else str(
                anchor_program.title.code))
            # commercial program theme code
            row_data.append('' if (
                    btag.content_type != "commercial" or anchor_program is None or anchor_program.program_genre is None or anchor_program.program_genre.program_theme is None) else str(
                anchor_program.program_genre.program_theme.code))
            # commercial program genre code
            row_data.append('' if (
                    btag.content_type != "commercial" or anchor_program is None or anchor_program.program_genre is None) else str(
                anchor_program.program_genre.code))
            # sport
            row_data.append('')
            # original or repeat
            row_data.append('')
            # live
            row_data.append("")
            # combined position in break
            row_data.append('0' if btag.content_type == "program" or not position_in_break else str(position_in_break))
            # combined count in break
            row_data.append('0')
            if btag.content_type != "program":
                combined_count_per_break_child_arr.append(ind)
            # promo program start time
            if btag.content_type=="promo":
                row_data.append(
                    '' if anchor_program is None else anchor_telecast_start_time)
            else:
                row_data.append("")
            # commercial program start time
            if btag.content_type=="commercial":
                row_data.append(
                    '' if anchor_program is None else anchor_telecast_start_time)
            else:
                row_data.append("")
            # spotid
            if btag.content_type=="commercial":
                h_mm = ('{:01x}'.format(int(mm))).upper()
                rand_i = randint(10**9, 10**10-1)
                row_data.append('9{}{}'.format(h_mm, rand_i))
            else:
                h_mm = ('{:01x}'.format(int(mm))).upper()
                rand_i = randint(10 ** 12, 10 ** 13 - 1)
                row_data.append('9{}{}'.format(h_mm, rand_i))
            # last modified date
            today = date_lib.today()
            row_data.append(today.strftime("%d/%m/%Y"))
            # ad breakcode
            if btag.content_type!="program" and anchor_program is not None:
                p_name = (anchor_program.title.name[0:4]).upper()
                p_code = anchor_program.title.code
                hh_ap = anchor_telecast_start_time.split(":")[0]
                mm_ap = anchor_telecast_start_time.split(":")[1]
                if int(mm_ap)>30:
                    mm_ap="00"
                    if hh_ap=="23":
                        hh_ap="00"
                    else:
                        hh_ap = "{0:02d}".format(int(hh_ap)+1)
                else:
                    mm_ap="30"
                b_pos = (chr(97+break_per_program)).upper()
                ad_break_code = "{}{}{}{}{}".format(p_name, p_code, hh_ap, mm_ap, b_pos)
                row_data.append(ad_break_code)
            else:
                row_data.append('')
            # promo broadcaster code
            row_data.append(
                '' if btag.content_type != "promo" or promo_channel is None or promo_channel.network is None else promo_channel.network.code)
            # beam
            row_data.append("")
            # split
            row_data.append("")
            # market
            row_data.append("")
            # split region
            row_data.append("")
            # split platform
            row_data.append("")
            # prod house
            if btag.content_type =="program":
                row_data.append("" if btag.content_type!="program" or obj.prod_house is None or obj.prod_house.code is None
                                else obj.prod_house.code)
            elif btag.content_type =="promo":
                row_data.append("0")
            else:
                row_data.append("")
            object_rows.append(row_data)
            prev_tag = btag
            prev_obj = obj

    if ext == "csv":
        file_name = "/tmp/{}_{}.csv".format(channel.channel_name, date).replace(' ', '_')
        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for r in object_rows:
                writer.writerow(r)
        email = EmailMessage(
            'Report for {} {}'.format(channel.channel_name, date),
            'Please Find attached the  report file\n\n',
            'aswin@tessact.com',
            (user_mail,'')
        )
        email.attach_file(file_name)
        email.send()
        silentremove(file_name)
    elif ext == "xml":
        top = ET.Element("BarcPlayoutMonitoring")
        tree = ET.ElementTree(top)
        for row_ind, row_data in enumerate(object_rows[1:len(object_rows)]):
            item = ET.SubElement(top, 'Item')
            for ind, d in enumerate(row_data):
                element_sub_item = ET.SubElement(item, header_row[ind])
                element_sub_item.text = str(d)
                if header_row[ind] in cdata_row:
                    element_sub_item.text = ET.CDATA(element_sub_item.text)
        file_name = "/tmp/{}_{}.xml".format(channel.channel_name, date).replace(' ', "_")
        indent(top)
        with open(file_name, 'wb') as xml_file:
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        email = EmailMessage(
            ' Report for {} {}'.format(channel.channel_name, date),
            'Please Find attached the report file\n\n',
            'aswin@tessact.com',
            (user_mail, '')
        )
        email.attach_file(file_name)
        email.send()
        silentremove(file_name)


@app.task
def send_program_master(user_mail, ext="csv"):
    if ext == "csv":
        file_name = "/tmp/ProgramMst.csv"
        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header_row = ["ChannelNameCode", "ChannelName", "Title", "TitleCode", "ContentLanguageCode", "ProgramThemeCode", "ProgramTheme", "ProgramGenreCode", "ProgramGenre", "ProdHouse"]
            object_rows = [header_row]
            p = Program.objects.all().select_related("channel", "program_genre", "title", "language")
            for pr in p:
                tmp = []
                tmp.append(pr.channel.code if pr.channel else "")
                tmp.append(pr.channel.name if pr.channel else "")
                tmp.append(pr.title.name if pr.title else "")
                tmp.append(pr.title.code if pr.title else "")
                tmp.append(pr.language.code if pr.language else "")
                tmp.append(pr.program_genre.program_theme.code if pr.program_genre and pr.program_genre.program_theme else "")
                tmp.append(pr.program_genre.program_theme.name if pr.program_genre and pr.program_genre.program_theme else "")
                tmp.append(pr.program_genre.code if pr.program_genre else "")
                tmp.append(pr.program_genre.name if pr.program_genre else "")
                tmp.append("")
                object_rows.append(tmp)
            for r in object_rows:
                writer.writerow(r)
        with open(file_name, 'rb') as csvfile:
            bucket_path = "barc-poc-content"
            f_path = 'masters/ProgramMaster.csv'
            s3_client.put_object(Body=csvfile, Bucket=bucket_path, Key=f_path)
        email = EmailMessage(
            'Program Master',
            'Please Find attached the program master file at https://s3.ap-south-1.amazonaws.com/barc-poc-content/'
            'masters/ProgramMaster.csv',
            'aswin@tessact.com',
            (user_mail,'')
        )
        email.send()
        silentremove(file_name)


@app.task
def send_promo_master(user_mail, ext="csv"):
    if ext == "csv":
        file_name = "/tmp/PromoMst.csv"
        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header_row = ["BrandNameCode", "BrandName", "Title", "TitleCode",
                          "BrandSector", "BrandSectorCode", "BrandCategory", "BrandCategoryCode",
                          "Advertiser", "AdvertiserCode", "AdvertiserGroup", "AdvertiserGroupCode",
                          "Descriptor", "DescriptorCode"]

            object_rows = [header_row]

            p = Promo.objects.all().select_related("channel", "brand_name", "title", "advertiser", "descriptor")
            for pr in p:
                tmp = []
                tmp.append(pr.brand_name.code if pr.brand_name else "")
                tmp.append(pr.brand_name.name if pr.brand_name else "")
                tmp.append(pr.brand_name.name if pr.brand_name else "")
                tmp.append(pr.brand_name.code if pr.brand_name else "")
                tmp.append(pr.brand_name.brand_category.brand_sector.name if pr.brand_name and pr.brand_name.brand_category and pr.brand_name.brand_category.brand_sector else "")
                tmp.append(pr.brand_name.brand_category.brand_sector.code if pr.brand_name and pr.brand_name.brand_category and pr.brand_name.brand_category.brand_sector else "")
                tmp.append(
                    pr.brand_name.brand_category.name if pr.brand_name and pr.brand_name.brand_category else "")
                tmp.append(
                    pr.brand_name.brand_category.code if pr.brand_name and pr.brand_name.brand_category else "")
                tmp.append(pr.advertiser.name if pr.advertiser else "")
                tmp.append(pr.advertiser.code if pr.advertiser else "")
                tmp.append(pr.advertiser.advertiser_group.name if pr.advertiser and pr.advertiser.advertiser_group else "")
                tmp.append(pr.advertiser.advertiser_group.code if pr.advertiser and pr.advertiser.advertiser_group else "")
                tmp.append(pr.descriptor.text if pr.descriptor else "")
                tmp.append(pr.descriptor.code if pr.descriptor else "")
                object_rows.append(tmp)
            for r in object_rows:
                writer.writerow(r)
        with open(file_name, 'rb') as csvfile:
            bucket_path = "barc-poc-content"
            f_path = 'masters/PromoMst.csv'
            s3_client.put_object(Body=csvfile, Bucket=bucket_path, Key=f_path)
        email = EmailMessage(
            'Program Master',
            'Please Find attached the promo master file at https://s3.ap-south-1.amazonaws.com/barc-poc-content/'
            'masters/PromoMaster.csv',
            'aswin@tessact.com',
            (user_mail,'')
        )
        email.send()
        silentremove(file_name)


@app.task
def send_commercial_master(user_mail, ext="csv"):
    if ext == "csv":
        file_name = "/tmp/CommercialMst.csv"
        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header_row = ["BrandNameCode", "BrandName", "Title", "TitleCode",
                          "BrandSector", "BrandSectorCode", "BrandCategory", "BrandCategoryCode",
                          "Advertiser", "AdvertiserCode", "AdvertiserGroup", "AdvertiserGroupCode",
                          "Descriptor", "DescriptorCode"]

            object_rows = [header_row]

            p = Commercial.objects.all().select_related("brand_name", "title", "advertiser", "descriptor")
            for pr in p:
                tmp = []
                tmp.append(pr.brand_name.code if pr.brand_name else "")
                tmp.append(pr.brand_name.name if pr.brand_name else "")
                tmp.append(pr.brand_name.name if pr.brand_name else "")
                tmp.append(pr.brand_name.code if pr.brand_name else "")
                tmp.append(pr.brand_name.brand_category.brand_sector.name if pr.brand_name and pr.brand_name.brand_category and pr.brand_name.brand_category.brand_sector else "")
                tmp.append(pr.brand_name.brand_category.brand_sector.code if pr.brand_name and pr.brand_name.brand_category and pr.brand_name.brand_category.brand_sector else "")
                tmp.append(
                    pr.brand_name.brand_category.name if pr.brand_name and pr.brand_name.brand_category else "")
                tmp.append(
                    pr.brand_name.brand_category.code if pr.brand_name and pr.brand_name.brand_category else "")
                tmp.append(pr.advertiser.name if pr.advertiser else "")
                tmp.append(pr.advertiser.code if pr.advertiser else "")
                tmp.append(pr.advertiser.advertiser_group.name if pr.advertiser and pr.advertiser.advertiser_group else "")
                tmp.append(pr.advertiser.advertiser_group.code if pr.advertiser and pr.advertiser.advertiser_group else "")
                tmp.append(pr.descriptor.text if pr.descriptor else "")
                tmp.append(pr.descriptor.code if pr.descriptor else "")
                object_rows.append(tmp)
            for r in object_rows:
                writer.writerow(r)
        with open(file_name, 'rb') as csvfile:
            bucket_path = "barc-poc-content"
            f_path = 'masters/CommercialMst.csv'
            s3_client.put_object(Body=csvfile, Bucket=bucket_path, Key=f_path)
        email = EmailMessage(
            'Program Master',
            'Please Find attached the commercial master file at https://s3.ap-south-1.amazonaws.com/barc-poc-content/'
            'masters/CommercialMst.csv',
            'aswin@tessact.com',
            (user_mail,'')
        )
        email.send()
        silentremove(file_name)


@app.task
def send_genre_master(user_mail, ext="csv"):
    header_row = ["PROGRAMGENRECODE", "PROGRAMGENRE", "PROGRAMTHEMECODE", "PROGRAMTHEME"]
    cdata_row = ["PROGRAMGENRE", "PROGRAMTHEME"]
    object_rows = [header_row]

    if ext == "csv":
        file_name = "/tmp/CommercialMst.csv"
        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header_row = ["PROGRAMGENRECODE", "PROGRAMGENRE", "PROGRAMTHEMECODE", "PROGRAMTHEME"]
            cdata_row = ["PROGRAMGENRE", "PROGRAMTHEME"]
            object_rows = [header_row]

            p = ProgramGenre.objects.all().select_related("program_theme")
            for pr in p:
                tmp = []
                tmp.append(pr.code if pr else "")
                tmp.append(pr.name if pr else "")
                tmp.append(pr.program_theme.code if pr.program_theme else "")
                tmp.append(pr.program_theme.name if pr.program_theme else "")

                object_rows.append(tmp)
            for r in object_rows:
                writer.writerow(r)
        with open(file_name, 'rb') as csvfile:
            bucket_path = "barc-poc-content"
            f_path = 'masters/GenreMst.csv'
            s3_client.put_object(Body=csvfile, Bucket=bucket_path, Key=f_path)
        email = EmailMessage(
            'Program Master',
            'Please Find attached the commercial master file at https://s3.ap-south-1.amazonaws.com/barc-poc-content/'
            'masters/CommercialMst.csv',
            'aswin@tessact.com',
            (user_mail, '')
        )
        email.send()
        silentremove(file_name)


@app.task
def send_mct(user_mail, start_date, end_date, ext="csv", ):

    file_name = "/tmp/MCT.csv"
    with open(file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        pt = PlayoutTag.objects.filter(video__channelclip__start_time__date__gte=start_date,
                                       video__channelclip__start_time__date__lte=end_date) \
            .order_by("video__channelclip__channel", "video__channelclip__start_time")
        for tag in pt:
            if isinstance(tag.tagged_object, Song):
                sobj = tag.tagged_object
                ch = ChannelClip.objects.filter(video=tag.video).first()
                writer.writerow([sobj.title, "Song", ch.channel.channel_name, sobj.language,
                                 ch.date, tag.start_time(), tag.end_time(),
                                 ", ".join([s.name for s in sobj.singers.all()]),
                                 ", ".join([s.name for s in sobj.actors.all()]), sobj.movie, sobj.genre, sobj.label,
                                 str(sobj.released_on)[0:4]])
    with open(file_name, 'rb') as csvfile:
        bucket_path = "music-downlink-data"
        f_path = 'MCT/MCT-{}-{}.csv'.format(start_date, end_date)
        s3_client.put_object(Body=csvfile, Bucket=bucket_path, Key=f_path)
    email = EmailMessage(
        'Program Master',
        'Please Find attached the commercial master file at https://s3.ap-south-1.amazonaws.com/music-downlink-data/'+f_path,
        'aswin@tessact.com',
        (user_mail, '')
    )
    email.send()
    silentremove(file_name)


def load_playout(url, code):

    tmp_file_name = os.path.join('/tmp/audio/', str(uuid.uuid4()) + '.xml')
    print(tmp_file_name)
    check_or_create_file(tmp_file_name)
    urlretrieve(url, tmp_file_name)
    dt = url.split("/")[-2]
    yr = int(dt.split('_')[2])
    mm = int(dt.split('_')[1])
    dd = int(dt.split('_')[0])
    start_datetime = datetime(year=yr, month=mm, day=dd) + timedelta(hours=2)
    end_datetime = datetime(year=yr, month=mm, day=dd) + timedelta(hours=26)
    channel_clips = ChannelClip.objects.filter(channel__channel_code=code, start_time__gte=start_datetime,
                                               end_time__lt=end_datetime).order_by('date', 'start_time')
    spec_channel = SpecChannel.objects.filter(code=code).first()
    for ch in channel_clips:
        pt = PlayoutTag.objects.filter(video=ch.video).delete()
    tree = ET.parse(tmp_file_name)
    root = tree.getroot()
    data = []
    for child in root:
        row_data = []
        for gc in child:
            # print(gc.tag)
            row_data.append(gc.text)
        data.append(row_data)
        # print("breaking", row_data)
        row_data = []
    p = None
    silentremove(tmp_file_name)
    for row_data in data:
        try:
            if row_data[1]=="Program":
                p = Program.objects.filter(title__name=row_data[7], channel=spec_channel).first()
                c = ContentType.objects.get(app_label='tags', model='program')

                if not p:
                    t, cr = Title.objects.get_or_create(name=row_data[7], code=row_data[8])
                    p, crp = Program.objects.get_or_create(title=t, channel=spec_channel)
            elif row_data[1]=="Promo":
                if "Sponsorship" in row_data[7]:
                    continue
                p = Promo.objects.filter(brand_name__name=row_data[7]).first()
                c = ContentType.objects.get(app_label='tags', model='promo')
                if not p:
                    t, cr = BrandName.objects.get_or_create(name=row_data[7], code=row_data[8])
                    p, crpr = Promo.objects.get_or_create(brand_name=t, channel=spec_channel)
            else:
                p = Commercial.objects.filter(title__name=row_data[7], descriptor__code=int(row_data[15])).first()
                c = ContentType.objects.get(app_label='tags', model='commercial')
                if not p:
                    t, cr = Title.objects.get_or_create(name=row_data[7], code=row_data[8])
                    bn = BrandName.objects.filter(code=row_data[39]).first()
                    p, crc = Commercial.objects.get_or_create(title=t, brand_name=bn)
            # print(p, c, row_data)
            if p:
                yy = int(row_data[10].split('/')[2])
                mm = int(row_data[10].split('/')[1])
                dd = int(row_data[10].split('/')[0])
                hh = int(row_data[12].split(':')[0])
                mn = int(row_data[12].split(':')[1])
                ss = int(row_data[12].split(':')[2])
                hh2 = int(row_data[13].split(':')[0])
                rand = 1 if random.random() > 0.1 else 0
                frame_in = (mn * 60 + ss) * 25 - 25 if (mn * 60 + ss) * 25 >= 25 else (mn * 60 + ss) * 25
                frame_in += rand * 25
                frame_out = (int(row_data[13].split(':')[1]) * 60 + int(row_data[13].split(':')[2])) * 25 - 25

                ch = ChannelClip.objects.filter(channel__channel_code=code,
                                                start_time=datetime(year=yy, month=mm, day=dd, hour=hh)).first()
                if ch and frame_in >= 0 and frame_out > 0:
                    if hh2==hh:
                        pt = PlayoutTag.objects.create(video=ch.video,
                                                       frame_in=frame_in,
                                                       frame_out=frame_out,
                                                       content_type=row_data[1].lower(),
                                                       object_content_type=c,
                                                       object_id=p.id
                                                       )
                        pt.save()
                    else:
                        pt = PlayoutTag.objects.create(video=ch.video,
                                                       frame_in=frame_in,
                                                       frame_out=3600*25,
                                                       content_type=row_data[1].lower(),
                                                       object_content_type=c,
                                                       object_id=p.id
                                                       )
                        ch = ChannelClip.objects.filter(channel__channel_code=code,
                                                        start_time=datetime(year=yy, month=mm, day=dd, hour=hh2)).first()
                        if hh2 and ch:
                            pt = PlayoutTag.objects.create(video=ch.video,
                                                           frame_in=0,
                                                           frame_out=frame_out,
                                                           content_type=row_data[1].lower(),
                                                           object_content_type=c,
                                                           object_id=p.id
                                                           )
        except MultipleObjectsReturned:
            if row_data[1]=="Program":
                c = ContentType.objects.get(app_label='tags', model='program')
                t, cr = Title.objects.get_or_create(name=row_data[7], code=row_data[8])
                p = Program.objects.filter(title=t, channel=spec_channel).first()
            elif row_data[1]=="Promo":
                if "Sponsorship" in row_data[7]:
                    continue
                c = ContentType.objects.get(app_label='tags', model='promo')
                t, cr = BrandName.objects.get_or_create(name=row_data[7], code=row_data[8])
                p = Promo.objects.filter(brand_name=t, channel=spec_channel).first()
            else:
                c = ContentType.objects.get(app_label='tags', model='commercial')
                t, cr = Title.objects.get_or_create(name=row_data[7], code=row_data[8])
                bn = BrandName.objects.filter(code=row_data[39]).first()
                p = Commercial.objects.filter(title=t, brand_name=bn).first()
            if p:
                yy = int(row_data[10].split('/')[2])
                mm = int(row_data[10].split('/')[1])
                dd = int(row_data[10].split('/')[0])
                hh = int(row_data[12].split(':')[0])
                mn = int(row_data[12].split(':')[1])
                ss = int(row_data[12].split(':')[2])
                hh2 = int(row_data[13].split(':')[0])
                rand = 1 if random.random() > 0.1 else 0
                frame_in = (mn*60+ss)*25 - 25 if (mn*60+ss)*25 >= 25 else (mn*60+ss)*25
                frame_in += rand*25
                frame_out = (int(row_data[13].split(':')[1])*60 + int(row_data[13].split(':')[2]))*25 - 25

                ch = ChannelClip.objects.filter(channel__channel_code=code, start_time=datetime(year=yy, month=mm, day=dd, hour=hh)).first()
                if ch and frame_in >= 0 and frame_out > 0:
                    if hh2==hh:
                        pt = PlayoutTag.objects.create(video=ch.video,
                                                       frame_in=frame_in,
                                                       frame_out=frame_out,
                                                       content_type=row_data[1].lower(),
                                                       object_content_type=c,
                                                       object_id=p.id
                                                       )
                        pt.save()
                    else:
                        pt = PlayoutTag.objects.create(video=ch.video,
                                                       frame_in=frame_in,
                                                       frame_out=3600*25,
                                                       content_type=row_data[1].lower(),
                                                       object_content_type=c,
                                                       object_id=p.id
                                                       )
                        ch = ChannelClip.objects.filter(channel__channel_code=code,
                                                        start_time=datetime(year=yy, month=mm, day=dd, hour=hh2)).first()
                        if hh2 and ch:
                            pt = PlayoutTag.objects.create(video=ch.video,
                                                           frame_in=0,
                                                           frame_out=frame_out,
                                                           content_type=row_data[1].lower(),
                                                           object_content_type=c,
                                                           object_id=p.id
                                                           )
            pass
        # if p:
        #     yy = int(row_data[11].split('/')[2])
        #     mm = int(row_data[11].split('/')[1])
        #     dd = int(row_data[11].split('/')[0])
        #     hh = int(row_data[13].split(':')[0])
        #     mn = int(row_data[13].split(':')[1])
        #     ss = int(row_data[13].split(':')[2])
        #     hh2 = int(row_data[14].split(':')[0])
        #     frame_in = (mn*60+ss)*25 - 25 if (mn*60+ss)*25 >= 25 else (mn*60+ss)*25
        #     frame_out = (int(row_data[14].split(':')[1])*60 + int(row_data[14].split(':')[2]))*25 - 25
        #
        #     ch = ChannelClip.objects.filter(channel__channel_code=code, start_time=datetime(year=yy, month=mm, day=dd, hour=hh)).first()
        #     if ch:
        #         if hh2==hh:
        #             pt = PlayoutTag.objects.create(video=ch.video,
        #                                            frame_in=frame_in,
        #                                            frame_out=frame_out,
        #                                            content_type=row_data[2].lower(),
        #                                            object_content_type=c,
        #                                            object_id=p.id
        #                                            )
        #             pt.save()
        #         else:
        #             pt = PlayoutTag.objects.create(video=ch.video,
        #                                            frame_in=frame_in,
        #                                            frame_out=3600*25,
        #                                            content_type=row_data[2].lower(),
        #                                            object_content_type=c,
        #                                            object_id=p.id
        #                                            )
        #             ch = ChannelClip.objects.filter(channel__channel_code=code,
        #                                             start_time=datetime(year=yy, month=mm, day=dd, hour=hh2)).first()
        #             if hh2 and ch:
        #                 pt = PlayoutTag.objects.create(video=ch.video,
        #                                                frame_in=0,
        #                                                frame_out=frame_out,
        #                                                content_type=row_data[2].lower(),
        #                                                object_content_type=c,
        #                                                object_id=p.id
        #                                                )
        #     # break
    # print(p)


def load_song(file, url=False):
    tmp_file = os.path.join("/tmp/",file.split("/")[-1])
    check_or_create_file(tmp_file)
    if url:
        with requests.get(file, stream=True) as r:
            with open(tmp_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    else:
        subprocess.run(["cp", file, tmp_file])
    with open(tmp_file, 'r+') as csv_file:
        spamreader = csv.reader(csv_file, delimiter=',', quotechar='|')
        headers = next(spamreader, None)
        for line in spamreader:
            try:
                song_title = line[0].upper()

                language = line[1].lower()

                movie_title = line[4].upper()
                print(line)
                yr = str(line[7]) if ("A" not in str(line[7]) and line[7]) else "2019"
                movie_obj, mov_created = Movie.objects.get_or_create(movie_title=movie_title, language=language,
                                                                     year_of_release="{}-01-01".format(yr))
                song_obj, song_created = Song.objects.get_or_create(title=song_title, movie=movie_obj,
                                                                    language=language)
                if song_created:
                    artists_names = line[2].upper().replace('"', '').split(";")
                    for art_name in artists_names:
                        per, pr_created = Person.objects.get_or_create(name=art_name.strip())
                        song_obj.singers.add(per)
                    actors_names = line[3].upper().replace('"', '').split(";")
                    for act_name in actors_names:
                        per, pr_created = Person.objects.get_or_create(name=act_name.strip())
                        song_obj.actors.add(per)
                    genre_names = line[5].upper().replace('"', '').split(";")
                    # for gen_name in genre_names:
                    #     gen, gn_created = Genre.objects.get_or_create(genre_name=gen_name.strip())
                    song_obj.genre = line[5].upper().replace('"', '')
                    label_names = line[6].upper()
                    if label_names:
                        lbl, lbl_created = Label.objects.get_or_create(name=label_names.strip())
                        song_obj.label = lbl
                    song_obj.save()
            except ValidationError:
                pass
            except ValueError:
                pass


@app.task
def move_file(src, dest):
    shutil.copy(src, dest)