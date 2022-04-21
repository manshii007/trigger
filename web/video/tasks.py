#  ~~~~~~~~
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#  ~~~~~~~~
#
from __future__ import absolute_import, unicode_literals

import base64
import codecs
import datetime
import difflib
from urllib.parse import unquote
import errno
import io
import json
import logging
import math
import operator
import os
import random
import re
import shutil
import socket
import subprocess as sp
import sys
import time
import urllib
import urllib.request
import uuid
from collections import OrderedDict, defaultdict
from datetime import date
from functools import reduce
from operator import and_, or_
from urllib.request import urlretrieve

import acoustid
import boto3
import botocore
import chromaprint
import cognitive_face as CF
import cv2
import librosa
from matplotlib.image import thumbnail
from matplotlib.pyplot import title
import numpy as np
import pandas as pd
import PIL
import requests
import scipy
import six
import sklearn
import subliminal
import tqdm
from babelfish import Language
from botocore.exceptions import ClientError
from celery import Celery, chain, chord, group
from celery.schedules import crontab
from celery.task import periodic_task
from content.models import (AssetVersion, Batch, Channel, CloudPerson,
                            Collection, Credit, Movie, Person, PersonGroup,
                            Promo, Rushes, Song, VideoProcessingStatus, File)
from contextual.models import Face, FaceGroup, HardCuts, VideoFaceGroup
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.mail import EmailMessage, send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
from frames.models import Frames, Rect, VideoFrame
from google.cloud import exceptions, language, speech, translate, vision
from google.cloud.speech import enums, types
from jobs.models import AutoVideoJob, JobType
from moviepy.editor import VideoFileClip
from PIL import Image
from publication.tasks import get_latest_publication, is_blacklisted
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table
import sklearn.externals
import joblib
from tags.models import (EmotionTag, FrameTag, GenericTag, KeywordTag, Logo,
                         LogoTag, ManualTag, MasterReportGen, OCRTag, CheckTag, CorrectionTag,
                         PlayoutTag, Tag, TagCategory, SpriteTag)
from tags.serializers import FrameTagSerializer
from thumbnails.models import Thumbnail
from tools.core.tools import hardcuts, image_to_azure_url, news_filter
from trigger_service import trigger_service_client
from users.models import User
from utils.constants import *
from utils.printing import NX_report, SonyReport
from wit import Wit

from video.serializers import DetailVideoSerializer

from .functions import get_cuts
from .models import Video, VideoProxyPath

from PIL import Image, ImageOps

from os import environ; environ["REGEX_DISABLED"] = "1"

try:  # attempt to use the Python 2 modules
    from urllib import urlencode

    from urllib2 import HTTPError, Request, URLError, urlopen
except ImportError:  # use the Python 3 modules
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

KEY = '33eb61dc944c4cb7917659502d6bc2d7'  # Replace with a valid subscription key (keeping the quotes in place).
CF.Key.set(KEY)

app = Celery('video')

ELASTIC_URL = os.getenv("ELASTIC", 'search-url')
bucket = os.getenv('BUCKET')
# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
IMAGE_LINK = "https://s3-display-images.s3.ap-south-1.amazonaws.com/"
ACCESS_TOKEN = "23TWEXXYFS4ALW2BWWJLTCX75NDXBKJJ"
wit_client = Wit(ACCESS_TOKEN)
FFPROBE_BIN = "ffprobe"
FFMPEG_BIN = "ffmpeg"
COMPLIANCE_THRESHOLD = 0.9
NUDITY_THRESHOLD = 0.1
SMOKING_THRESHOLD = 0.3
DRUGS_THRESHOLD = 0.3
ALCOHOL_THRESHOLD = 0.2
FIRE_THRESHOLD = 0.4
SEXDOLLS_THRESHOLD = 0.3
FLAG_THRESHOLD = 0.3
STATUE_THRESHOLD = 0.9
JUMP = 0.5
RECOGNITION_ARN = "arn:aws:iam::364083382040:role/awsrekognition"
EMOTION_CONFIDENCE = 0.7
OBJECT_CONFIDENCE = 0.5

complaince_models = [
"nudity",
"sexdolls",
"alcohol",
"nakedstatue",
"flag",
"drugs",
"smoking",
"fire",
"blood"
]

compliance_tags = ["Compliance" ,"Programming", "Drugs", "Alcohol", "Fire", "Sex Dolls", "Indian Flag", "Naked Statue", "Nudity", "Smoking", "Blood"]


barred_detections = ["BONG"]

asset_mapping = {
        'movies': Movie,
        'rushes': Rushes,
        'promos': Promo,
    }

logger = logging.getLogger('debug')

s3 = boto3.client('s3')
# aws_client = boto3.client('rekognition', region_name="us-east-1")

banned_words = ["Human", "Person", "Woman", "People", "Portrait" "Electrical Device", ""]

es = Elasticsearch(
    hosts = [{'host': ELASTIC_URL, 'port': 443}],
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)


class RequestError(Exception):
    pass

def check_or_create_file(file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

def image_exists_s3(path):
    r = requests.head(path)
    return r.status_code == requests.codes.ok

def get_display_images_link(object_name):
    image_name = "{}.jpg".format(object_name.upper().strip().replace(" ", "+"))
    object_link = IMAGE_LINK + image_name
    if image_exists_s3(object_link):
        return object_link
    else:
        return None

def create_sagemaker_endpoint(endpoint_name):
    os.system("aws sagemaker create-endpoint --endpoint-name '{}' --endpoint-config-name '{}'".format(endpoint_name, endpoint_name))

def delete_sagemaker_endpoint(endpoint_name):
    os.system("aws sagemaker delete-endpoint --endpoint-name '{}'".format(endpoint_name))

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occurred

@app.task()
def create_all_endpoints():
    for model in complaince_models:
        create_sagemaker_endpoint(model)
        time.sleep(5)

@app.task()
def delete_all_endpoints():
    for model in complaince_models:
        delete_sagemaker_endpoint(model)
        time.sleep(5)

def close_clip(clip):
    try:
        clip.reader.close()
        del clip.reader
        if clip.audio != None:
            clip.audio.reader.close_proc()
            del clip.audio
        del clip
    except Exception as e:
        sys.exc_clear()


def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)

def wit_entity_call(query):
    search_dict = {"contact" : [], "ocr": [], "stt": [], "emotion": [], "object": [], "shots": [], "location": []}
    message = wit_client.message(query.lower())
    for key, entity in message["entities"].items():
        for val in entity:
            if entity in ['contact', 'object', 'shots', 'location']:
                search_dict[val['role']].append(val["value"].upper())
            else:
                search_dict[val['role']].append(val["value"])
    return search_dict

def save_video_local(input_file):

    tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4()) + '.mp4')
    print(tmp_file_name)
    check_or_create_file(tmp_file_name)
    with requests.get(input_file, stream=True) as r:
        with open(tmp_file_name, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return tmp_file_name

def create_audio(video_path):

    file_name = os.path.join('/tmp/audio/', str(uuid.uuid4()) + '.wav')
    check_or_create_file(file_name)
    command = [FFMPEG_BIN,
               '-v', 'quiet',
               '-i', video_path,
               '-ac', '1',
               '-acodec', 'pcm_s16le', '-ar', '16000',
               file_name, '-y']
    output = sp.check_output(command)
    silentremove(video_path)
    return file_name


def get_bucket_key_s3(url, title):
    file = url.strip("https://")
    bucket = file.split(".")[0]
    key = os.path.join("/".join(file.split("/")[1:-1]), title)
    return bucket, key

@app.task()
def process_for_objects_aws(video_instance):
    job_type_instance, _ = JobType.objects.get_or_create(name='Identify Objects AWS')
    auto = AutoVideoJob.objects.create(video=video_instance,
                                       job_type=job_type_instance, eta=0)

@app.task()
def process_for_face_detect(video_id):
    video_instance = Video.objects.get(pk=video_id)
    job_type_instance, _ = JobType.objects.get_or_create(name='Identify Faces')
    auto = AutoVideoJob.objects.create(video=video_instance,
                                       job_type=job_type_instance, eta=0)

@app.task()
def process_for_emotions_aws(video_instance):
    job_type_instance, _ = JobType.objects.get_or_create(name='Identify Emotion AWS')
    auto = AutoVideoJob.objects.create(video=video_instance,
                                       job_type=job_type_instance, eta=0)

@app.task()
def process_for_emotion(video_id):
    video_instance = Video.objects.get(pk=video_id)
    job_type_instance, _ = JobType.objects.get_or_create(name='Identify Emotion')
    auto = AutoVideoJob.objects.create(video=video_instance,
                                       job_type=job_type_instance, eta=0)


def create_presigned_url(object_name, bucket_name=bucket, expiration=25200):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    session = boto3.session.Session(region_name='ap-south-1')
    s3client = session.client('s3', config= boto3.session.Config(signature_version='s3v4'))
    try:
        response = s3client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

def s3_signed_url(file, title):
    bucket, key = get_bucket_key_s3(file, title)
    signed_url = create_presigned_url(key, bucket)
    if signed_url:
        return signed_url
    else:
        return None

def get_s3_signed_url(key):
    signed_url = create_presigned_url(key)
    if signed_url:
        return signed_url
    else:
        return None

def resize_image(filename, size):
    image = Image.open(filename)
    image = image.resize(size, Image.ANTIALIAS)
    image.save(filename)
    return filename

def upload_thumbnail(video_id, duration, input_file):
    file = '/tmp/{}.png'.format(video_id)
    command_frame_extraction = [FFMPEG_BIN,
                            '-v', 'quiet',
                            '-i', input_file,
                            '-vf', 'select=gte(n\,{})'.format(int(float(duration)//2)),
                            '-vframes', '1',
                            file]
    output = sp.check_output(command_frame_extraction)
    size = (42,42) #predefined size for thumbnails.
    file = resize_image(file, size)
    time_stamp = str(int(time.time()))
    output_file = file.split("/")[-1].split(".")[0] + "_" + time_stamp + "." + file.split("/")[-1].split(".")[1]
    upload_data = s3.upload_file(file, bucket, "Thumbnails/" + output_file)
    url = "https://{}.s3.ap-south-1.amazonaws.com/Thumbnails/{}".format('trigger-uploaded-videos', output_file)
    os.remove(file)
    return url

def create_asset(bucket, key, title):
    file_extensions = set(["mp4", "mxF", "mov", "MTS", "mts", "mxf"])
    original_file_name = key.split(".")
    asset_objects = key.split("/")
    url = "https://{}.s3.ap-south-1.amazonaws.com/{}".format(bucket, key)
    if original_file_name[-1] in file_extensions:
        channel = Channel.objects.filter(channel_name__iexact=asset_objects[0]).first()
        asset_type = asset_objects[1]
        if not title:
            title = asset_objects[-1]
        content = asset_mapping[asset_type].objects.create(title=title, channel=channel, ingested_on=str(datetime.datetime.today().date()))
        video = Video.objects.create(title=title, file=url)
        if asset_type == 'movies':
            asset_type = 'movie'
        content_type = ContentType.objects.filter(model=asset_type).first()
        asset = AssetVersion.objects.create(title=title, version_number=0, object_id=content.id, content_type=content_type, video=video, is_active=True)

# def generate_video_sprites(columns, rows, size, framesPath='/tmp/frames', video_id=None):
#     masterWidth = int(420 * columns)
#     masterHeight = int(420*(size[1]/size[0]) * rows)

#     num_of_images = columns*rows
#     line, column, mode = 0, 0, 'RGBA'
#     try:
#         finalImage = Image.new(mode=mode, size=(masterWidth, masterHeight), color=(0, 0, 0, 0))
#         finalImage.save(os.path.join('/tmp',"{}.png".format(video_id)))
#     except IOError:
#         print("IOError")
#         mode = 'RGB'
#         finalImage = Image.new(mode=mode, size=(masterWidth, masterHeight))

#     filesMap = ["{}-{}.png".format(video_id,file_num+1) for file_num in range(0, 125)]

#     for filename in filesMap:
#         filepath = os.path.join(framesPath, filename)
#         try:
#             with Image.open(filepath) as image:
#                 l_size = 420, int(420 * size[1]/size[0])
#                 # image.thumbnail(l_size, Image.ANTIALIAS)
#                 thumb = ImageOps.fit(image, l_size, Image.ANTIALIAS)

#                 locationX = l_size[0] * column
#                 locationY = l_size[1] * line

#                 finalImage.paste(thumb, (locationX, locationY))

#                 column += 1

#                 if column == columns:
#                     line += 1
#                     column = 0
#         except FileNotFoundError as e:
#             print(e)
#             column +=1
#             if column == columns:
#                 line += 1
#                 column = 0
#             pass

#     finalImage.save(os.path.join('/tmp',"{}.png".format(video_id)))

# def makingthumbnail_forshowing(video, total_frames, video_id):
#     skip = math.ceil(total_frames/125)
#     generated_images = bash('ffmpeg -i {} -f image2 -vsync vfr -vf \"select=\'not(mod(n,{})\')\" -vframes 125 {}'.format(video, skip,'/tmp/frames/{}-%d.png').format(video_id)) 
#     generate_video_sprites(columns, rows, size, framesPath='/tmp/frames', video_id=video_id) 


@app.task
def set_metadata(input_file, video_id):
    """
    Takes the file path and video id, sets the metadata
    :param input_file: file url or file path
    :param video_id: video id of the file
    :return: True
    """
    command = [FFPROBE_BIN,
               '-v', 'quiet',
               '-print_format', 'json',
               '-show_format',
               '-show_streams',
               '-select_streams', 'v:0',
               input_file]
    print(datetime.datetime.now())
    output = sp.check_output(command)
    output = output.decode('utf-8')
    metadata_output = json.loads(output)
    video_instance = Video.objects.get(pk=video_id)
    stream = metadata_output['streams'][0]
    tot_frames_junk = int(stream['avg_frame_rate'].split("/")[0])
    tot_time_junk = int(stream['avg_frame_rate'].split("/")[1])
    # update the video model with newly acquired metadata
    video_instance.width = stream['width']
    video_instance.height = stream['height']
    video_instance.frame_rate = tot_frames_junk/tot_time_junk
    video_instance.duration = stream['duration']
    try:
        video_instance.bitrate = stream['bit_rate']
    except:
        video_instance.bitrate = metadata_output['format']['bit_rate']
    video_instance.video_codec = stream['codec_name']
    file_size = urllib.request.urlopen(video_instance.file).length
    video_instance.size =  file_size/1024/1024
    try:
        video_instance.total_frames = stream['nb_frames']
    except KeyError:
        total_frames = float(stream['duration'])*tot_frames_junk/tot_time_junk
        video_instance.total_frames = total_frames
    video_instance.video_codec = stream['codec_name']
    video_instance.save()
    try:
        picture = upload_thumbnail(video_id, video_instance.duration, input_file)
        Thumbnail.objects.create(content_object=video_instance, url=picture)
    except:
        pass
    file = File.objects.filter(video_id=video_id)
    if file:
        file = file.first()
        if file.file_metadata:
            file.file_metadata['Technical Metadata Tab']['Codec -- Y'] = stream['codec_name']
            file.file_metadata['Technical Metadata Tab']['Bitrate -- Y'] = video_instance.bitrate
            file.save() 

    # try:
    #     makingthumbnail_forshowing(input_file, video_instance.total_frames, video_id)
    # except:
    #     pass

    return True


def detect_object(contents):
    """Detects text in the file."""
    base64_bytes = base64.b64encode(contents)

    # third: decode these bytes to text
    # result: string (in utf-8)
    base64_string = base64_bytes.decode('utf-8')

    request = {
        'image': {
            "content": base64_string
        },
        'features': [{'type': "OBJECT_LOCALIZATION", "maxResults": 10}],

    }
    r = requests.post("https://vision.googleapis.com/v1/images:annotate?key=AIzaSyCfSAsgK_3Fm2s4a2_tYrXpKj0AZOD_oDM",
                      data=json.dumps(
                          {
                              "requests": [
                                  request
                              ]
                          }
                      ))
    response = r.json()
    print(response)
    fin_labels = []
    try:

        labels = response['responses'][0]['localizedObjectAnnotations']

        for label in labels:
            if label['name']=="car":
                if label['score']>0.8:
                    fin_labels.append("car - prominent")
                else:
                    fin_labels.append("car - not prominent")
            else:
                fin_labels.append(label['name'])

        return fin_labels
    except KeyError:
        return fin_labels

def failure_response(self, exc, task_id, args, kwargs, einfo):
    print(args)
    print(kwargs)
    print("failed")
    #get job id
    try:
        job_id = str(args[2])
        auto_job = AutoVideoJob.objects.get(id=job_id)
        auto_job.job_status = 'FAI'
        auto_job.eta = 0.0
        auto_job.save()
    except:
        pass
    print("status updated")
    try:
        file_name = str(args[-1])
        silentremove(file_name)
    except:
        pass

@app.task(on_failure=failure_response)
def get_objects_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_time = slot - 1
    slot_time = current_time
    current_frame = myclip.get_frame(slot_time)

    j = PIL.Image.fromarray(current_frame)
    #with open("./utils/objects.txt", 'r') as fd:
    #    filter_list = [f.strip() for f in fd.readlines()]
    with io.BytesIO() as output:
        j.save(output, format="PNG")
        contents = output.getvalue()
        labels = detect_object(contents)
    for label in labels:
        print('{} '.format(label))
        others_tag = GenericTag.objects.filter(title__iexact="Others").first()
        if not others_tag:
            others_tag = GenericTag.objects.filter(title="Others", parent=None)
        tag_obj = GenericTag.objects.filter(title__iexact=label).first()
        if not tag_obj:
            tag_obj = GenericTag.objects.create(title=label, parent=others_tag)
        frame_tag_obj = FrameTag.objects.create(tag=tag_obj, video=get_object_or_404(Video, pk=video_id),
                                                        frame_in=int((slot - 1) * (video_obj.frame_rate)),
                                                        frame_out=int(slot * (video_obj.frame_rate)), words=label)
        frame_tag_obj.save()
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += (1 / video_obj.duration)
    auto_job.save()
    close_clip(myclip)

@app.task
def merge_object_detections(video_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    tags = video_obj.frametag.all().exclude(tag__parent__title__iexact="Programming").order_by('frame_in')

    output = []
    for x in tags:
        if x.tag.title not in output:
            output.append(x.tag.title)
    for tag_name in output:
        this_tags = tags.filter(tag__title__iexact=tag_name).order_by('frame_in')
        tmp_keyword = None
        for object_tag in this_tags:
            if not tmp_keyword:
                tmp_keyword = object_tag
            else:
                if object_tag.frame_in == tmp_keyword.frame_out:
                    object_tag.frame_in = tmp_keyword.frame_in
                    object_tag.save()
                    tmp_keyword.delete()
                    tmp_keyword = object_tag
                else:
                    tmp_keyword = object_tag


@app.task(on_failure=failure_response)
def background_video_processing(input_file, video_id, job_id, tmp_file_name):
    # tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4()) + '.mp4')
    print(tmp_file_name)
    check_or_create_file(tmp_file_name)
    urlretrieve(input_file, tmp_file_name)
    with requests.get(input_file, stream=True) as r:
        with open(tmp_file_name, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    video_obj = get_object_or_404(Video, pk=video_id)
    frame_tags = FrameTag.objects.all().filter(video=video_obj)
    for frame_tag in frame_tags:
        frame_tag.delete()
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    # tags = trigger_service_client.guide_process_video(input_file)
    # for tag in tags:
    #     print(tag)
    #     try:
    #         tc = TagCategory.objects.get(name="Others")
    #         tag_obj, present = Tag.objects.get_or_create(name=", ".join(tag.labels), category=tc)
    #     except MultipleObjectsReturned :
    #         tag_obj = Tag.objects.all().filter(name=" ,".join(tag.labels))[0]
    #     frame_tag_obj = FrameTag.objects.create(tag=tag_obj, video=get_object_or_404(Video, pk=video_id),
    #                                             frame_in=tag.start_frame, frame_out=tag.end_frame)
    #     frame_tag_obj.save()
    # auto_job.job_status = 'PRD'
    # auto_job.save()
    # # chord is used because no task should wait for another task to complete
    for st in range(1, int(video_obj.duration)):
        get_objects_in_slot(st, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    merge_object_detections.delay(video_id)
    index_objects.delay(video_id)


@app.task
def background_video_processing_samosa(input_file, video_id, job_id):
    # tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4()) + '.mp4')
    # print(tmp_file_name)
    # check_or_create_file(tmp_file_name)
    # urlretrieve(input_file, tmp_file_name)
    # with requests.get(input_file, stream=True) as r:
    #     with open(tmp_file_name, 'wb') as f:
    #         shutil.copyfileobj(r.raw, f)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    video_obj = get_object_or_404(Video, pk=video_id)
    frame_tags = FrameTag.objects.all().filter(video=video_obj)
    for frame_tag in frame_tags:
        frame_tag.delete()
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    tags = trigger_service_client.guide_process_video_samosa(input_file)
    for tag in tags:
        print(tag)
        try:
            tc = TagCategory.objects.get(name="Others")
            tag_obj, present = Tag.objects.get_or_create(name=", ".join(tag.labels), category=tc)
        except MultipleObjectsReturned :
            tag_obj = Tag.objects.all().filter(name=" ,".join(tag.labels))[0]
        frame_tag_obj = FrameTag.objects.create(tag=tag_obj, video=get_object_or_404(Video, pk=video_id),
                                                frame_in=tag.start_frame, frame_out=tag.end_frame)
        frame_tag_obj.save()
    auto_job.job_status = 'PRD'
    auto_job.save()
    # # chord is used because no task should wait for another task to complete
    # res = chord(
    #     (get_objects_in_slot.s(st, tmp_file_name, video_id, auto_job.id) for st in range(1, int(video_obj.duration)*5)),
    #     chord_clean_video_file.s(tmp_file_name, job_id))
    # # res_clean = chain(res, merge_object_detections.s(video_id))
    # res.apply_async()


@app.task
def background_video_processing_logo(input_file, video_id, job_id):
    # tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4()) + '.mp4')
    # print(tmp_file_name)
    # check_or_create_file(tmp_file_name)
    # urlretrieve(input_file, tmp_file_name)
    # with requests.get(input_file, stream=True) as r:
    #     with open(tmp_file_name, 'wb') as f:
    #         shutil.copyfileobj(r.raw, f)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    video_obj = get_object_or_404(Video, pk=video_id)
    frame_tags = LogoTag.objects.all().filter(video=video_obj)
    for frame_tag in frame_tags:
        frame_tag.delete()
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    tags = trigger_service_client.guide_process_video(input_file)
    for tag in tags:
        print(tag)
        try:
            tc = TagCategory.objects.get(name="Others")
            tag_obj, present = Logo.objects.get_or_create(name=", ".join(tag.labels))
        except MultipleObjectsReturned :
            tag_obj = Tag.objects.all().filter(name=" ,".join(tag.labels))[0]
        frame_tag_obj = LogoTag.objects.create(tag=tag_obj, video=get_object_or_404(Video, pk=video_id),
                                                frame_in=tag.start_frame, frame_out=tag.end_frame)
        frame_tag_obj.save()
    auto_job.job_status = 'PRD'
    auto_job.save()

def detect_location(img):
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    response = runtime.invoke_endpoint(
        EndpointName='location',
        ContentType='application/x-image',
        Body=bytearray(img)
        )
    result = response['Body'].read().decode("utf-8")
    result = json.loads(result)['locations']
    return result

def detect_logo(img):
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    response = runtime.invoke_endpoint(
        EndpointName='logo',
        ContentType='application/x-image',
        Body=bytearray(img)
        )
    classes = ["SAMSUNG", "APPY FIZZ"]
    result = response['Body'].read().decode("utf-8")
    result = json.loads(result)
    predictions = []
    if result['classes']:
        predictions = [classes[x] for x in result['classes'][0]]
    return predictions

def visualize_detection(dets):
        """
        get bounding-box coordinates to visualize detections in one image
        
        Parameters:
        ----------
        img : numpy.ndarray
        dets : numpy.array
            ssd detections, numpy.array([[id, score, xmin, ymin, xmax, ymax]...])
            each row is one object
            xmin, ymin, xmax, ymax are expressed as ratio of image widthand height
        
        Returns:
        -------
        x,y,width,height : float
            expressed as ratio (%)
            x, y are the coordinates of top left corner of bounding box
            width, height are values for the bounding box
        img_width, img_height : float
            size of the image
        """
        # reading image
        # for storing all the percent values of bounding-box coordinates 
        ( _, _, xmin, ymin, xmax, ymax) = dets
        # getting x,y,width,height in %
        x = xmin
        y= ymin
        width = xmax - xmin
        height = ymax - ymin

        return [x,y,width,height]

class AwsVideoDetect:
    jobId = ''
    rek = boto3.client('rekognition', region_name='ap-south-1')
    sqs = boto3.client('sqs', region_name='ap-south-1')
    sns = boto3.client('sns', region_name='ap-south-1')

    roleArn = ''
    bucket = ''
    video = ''
    startJobId = ''

    sqsQueueUrl = ''
    snsTopicArn = ''
    processType = ''

    def __init__(self, role, bucket, video):    
        self.roleArn = role
        self.bucket = bucket
        self.video = video


    def GetSQSMessageSuccess(self):

        jobFound = False
        succeeded = False

        dotLine=0
        while jobFound == False:
            sqsResponse = self.sqs.receive_message(QueueUrl=self.sqsQueueUrl, MessageAttributeNames=['ALL'],
                                          MaxNumberOfMessages=10)

            if sqsResponse:
                
                if 'Messages' not in sqsResponse:
                    if dotLine<40:
                        print('.', end='')
                        dotLine=dotLine+1
                    else:
                        print()
                        dotLine=0    
                    sys.stdout.flush()
                    time.sleep(5)
                    continue

                for message in sqsResponse['Messages']:
                    notification = json.loads(message['Body'])
                    rekMessage = json.loads(notification['Message'])
                    print(rekMessage['JobId'])
                    print(rekMessage['Status'])
                    if rekMessage['JobId'] == self.startJobId:
                        print('Matching Job Found:' + rekMessage['JobId'])
                        jobFound = True
                        if (rekMessage['Status']=='SUCCEEDED'):
                            succeeded=True

                        self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                       ReceiptHandle=message['ReceiptHandle'])
                    else:
                        print("Job didn't match:" +
                              str(rekMessage['JobId']) + ' : ' + self.startJobId)
                    # Delete the unknown message. Consider sending to dead letter queue
                    self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                   ReceiptHandle=message['ReceiptHandle'])


        return succeeded

    def StartFaceDetection(self):
        response=self.rek.start_face_detection(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
            NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn}, FaceAttributes='ALL')

        self.startJobId=response['JobId']
        print('Start Job Id: ' + self.startJobId)

    def GetFaceDetectionResults(self):
        maxResults = 1000
        paginationToken = ''
        finished = False
        object_data = {}
        first_check = True
        while finished == False:
            response = self.rek.get_face_detection(JobId=self.startJobId,
                                            MaxResults=maxResults,
                                            NextToken=paginationToken)
            if first_check:
                object_data = response
                first_check = False
            else:
                object_data["Faces"] += response["Faces"]

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True

        return object_data

    def StartFaceSearchCollection(self):
        response=self.rek.start_face_search(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
            NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn}, CollectionId="Collection")

        self.startJobId=response['JobId']
        print('Start Job Id: ' + self.startJobId)

    def GetFaceSearchCollectionResults(self):
        response = self.rek.get_face_search(JobId=self.startJobId)

        return response

    def StartLabelDetection(self):
        response=self.rek.start_label_detection(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
            NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})

        self.startJobId=response['JobId']
        print('Start Job Id: ' + self.startJobId)


    def GetLabelDetectionResults(self):
        maxResults = 1000
        paginationToken = ''
        finished = False
        object_data = {}
        first_check = True
        while finished == False:
            response = self.rek.get_label_detection(JobId=self.startJobId,
                                            MaxResults=maxResults,
                                            NextToken=paginationToken,
                                            SortBy='TIMESTAMP')
            if first_check:
                object_data = response
                first_check = False
            else:
                object_data["Labels"] += response["Labels"]

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True

        return object_data

    def CreateTopicandQueue(self):
      
        millis = str(int(round(time.time() * 1000)))

        #Create SNS topic
        
        snsTopicName="AmazonRekognitionExample" + millis

        topicResponse=self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse['TopicArn']

        #create SQS queue
        sqsQueueName="AmazonRekognitionQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']

        attribs = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                                    AttributeNames=['QueueArn'])['Attributes']
                                        
        sqsQueueArn = attribs['QueueArn']

        # Subscribe SQS queue to SNS topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
            Protocol='sqs',
            Endpoint=sqsQueueArn)

        #Authorize SNS to write SQS queue 
        policy = """{{
              "Version":"2012-10-17",
              "Statement":[
                {{
                  "Sid":"MyPolicy",
                  "Effect":"Allow",
                  "Principal" : {{"AWS" : "*"}},
                  "Action":"SQS:SendMessage",
                  "Resource": "{}",
                  "Condition":{{
                    "ArnEquals":{{
                      "aws:SourceArn": "{}"
                    }}
                  }}
                }}
              ]
            }}""".format(sqsQueueArn, self.snsTopicArn)

        response = self.sqs.set_queue_attributes(
            QueueUrl = self.sqsQueueUrl,
            Attributes = {
                'Policy' : policy
            })

    def DeleteTopicandQueue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)

def get_bucket_video_key_s3(url):
    match = re.search('^https?://([^.]+).s3.ap-south-1.amazonaws.com/(.*)', url)
    if match:
        return match.group(1), match.group(2).replace("+", " ").replace("%3A", ":").replace("%5B", "[").replace("%5D", "]")
    return None, None

def detect_objects_aws(input_file):

    bucket, video_key = get_bucket_video_key_s3(input_file)
    analyzer = AwsVideoDetect(RECOGNITION_ARN, bucket, video_key)
    analyzer.CreateTopicandQueue()
    analyzer.StartLabelDetection()
    if analyzer.GetSQSMessageSuccess()==True:
        object_data = analyzer.GetLabelDetectionResults()
    analyzer.DeleteTopicandQueue()
    return object_data    

def detect_face_aws(input_file):

    bucket, video_key = get_bucket_video_key_s3(input_file)
    analyzer = AwsVideoDetect(RECOGNITION_ARN, bucket, video_key)
    analyzer.CreateTopicandQueue()
    analyzer.StartFaceDetection()
    if analyzer.GetSQSMessageSuccess()==True:
        face_data = analyzer.GetFaceDetectionResults()
    analyzer.DeleteTopicandQueue()
    return face_data

def search_face_aws(input_file):

    bucket, video_key = get_bucket_video_key_s3(input_file)
    analyzer = AwsVideoDetect(RECOGNITION_ARN, bucket, video_key)
    analyzer.CreateTopicandQueue()
    analyzer.StartFaceSearchCollection()
    if analyzer.GetSQSMessageSuccess()==True:
        face_data = analyzer.GetFaceSearchCollectionResults()
    analyzer.DeleteTopicandQueue()
    return face_data


def detect_object_sagemaker(img):
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    response = runtime.invoke_endpoint(                                                         
        EndpointName='object',                                                                
        ContentType='application/x-image',                                                      
        Body=bytearray(img)                                                                     
        )                                                                                       
    result = response['Body'].read().decode("utf-8")                                            
    result = json.loads(result)['outputs']
    detections = result['num_detections'][0]
    pred_labels = set(result['detection_classes'][0][:int(detections)])
    labels = [category_index[x]['name'] for x in pred_labels]

    return labels


def set_objects_aws(object_json, video_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    frame_rate = object_json["VideoMetadata"]["FrameRate"]
    top = 0
    left = 0
    width = 0
    height = 0
    for object_instance in object_json["Labels"]:
        label = object_instance["Label"]["Name"]
        frame_in = int((object_instance["Timestamp"] / 1000) * frame_rate)
        frame_out = frame_in + 12
        confidence = object_instance["Label"]["Confidence"] / 100
        if confidence >= OBJECT_CONFIDENCE:
            if label.upper() not in barred_objects:
                print('{} '.format(label))
                others_tag = GenericTag.objects.filter(title__iexact="Others").first()
                if not others_tag:
                    others_tag = GenericTag.objects.filter(title="Others", parent=None)
                tag_obj = GenericTag.objects.filter(title__iexact=label).first()
                if not tag_obj:
                    tag_obj = GenericTag.objects.create(title=label, parent=others_tag)
                if "Instances" in object_instance["Label"]:
                    if object_instance["Label"]["Instances"]:
                        for label_instance in object_instance["Label"]["Instances"]:
                            top = label_instance["BoundingBox"]["Top"]
                            left = label_instance["BoundingBox"]["Left"]
                            width = label_instance["BoundingBox"]["Width"]
                            height = label_instance["BoundingBox"]["Height"]
                            frame_tag_obj = FrameTag.objects.create(tag=tag_obj, video=get_object_or_404(Video, pk=video_id),
                                                                    frame_in=frame_in,
                                                                    frame_out=frame_out, words=label, confidence=confidence, up_left_x=top, up_left_y=left, height=height, width=width)
                            frame_tag_obj.save()
                    else:
                        frame_tag_obj = FrameTag.objects.create(tag=tag_obj, video=get_object_or_404(Video, pk=video_id),
                                                                    frame_in=frame_in,
                                                                    frame_out=frame_out, words=label, confidence=confidence, up_left_x=top , up_left_y=left , height=height , width=width)
                        frame_tag_obj.save()


def set_emotions_aws(face_json, video_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    frame_rate = face_json["VideoMetadata"]["FrameRate"]
    for face_instance in face_json["Faces"]:
        emotion_dict = face_instance["Face"]["Emotions"]
        if emotion_dict:
            frame_in = int((face_instance["Timestamp"] / 1000) * frame_rate)
            frame_out = frame_in + 12
            emotion = emotion_dict[0]["Type"]
            confidence = emotion_dict[0]["Confidence"] / 100
            if confidence >= EMOTION_CONFIDENCE:
                emotion_tag = EmotionTag.objects.create(frame_in=frame_in,
                                          frame_out=frame_out,
                                          emotion_quo=emotion,
                                          video=video_obj,
                                          confidence=confidence)
                emotion_tag.save()

@app.task
def background_video_processing_aws_objects(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    object_json = detect_objects_aws(video_obj.file)
    set_objects_aws(object_json, video_id)
    video_obj.aws_object_json = object_json
    video_obj.save()
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta = 1
    auto_job.job_status = 'PRD'
    auto_job.save()
    index_objects.delay(video_id)

@app.task
def background_video_processing_aws_emotions(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    face_json = detect_face_aws(video_obj.file)
    set_emotions_aws(face_json, video_id)
    video_obj.aws_face_json = face_json
    video_obj.save()
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta = 1
    auto_job.job_status = 'PRD'
    auto_job.save()
    index_emotions_aws.delay(video_id)


def detect_nudity_classify(img):
    labels = []
    object_categories = [
    'Exposed Belly', 
    'Exposed Buttocks', 
    'Exposed Breast Female', 
    'Exposed Genitalia Female', 
    'Exposed Breast Male', 
    'Exposed Genitalia Male'
    ]
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    response = runtime.invoke_endpoint(
        EndpointName='nudity',
        ContentType='application/x-image',
        Body=bytearray(img)
        )
    result = response['Body'].read().decode("utf-8")
    result = json.loads(result)['prediction']
    for label in result:
        if label[1] >= NUDITY_THRESHOLD:
            labels.append([object_categories[int(label[0])],visualize_detection(label)])
    return labels

def detect_smoke_classify(img):
    labels = []
    object_categories = [
    'cigarette',
    'pipe',
    'bong',
    'ashtray'
    ]
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    response = runtime.invoke_endpoint(
        EndpointName='smoking',
        ContentType='application/x-image',
        Body=bytearray(img)
        )
    result = response['Body'].read().decode("utf-8")
    result = json.loads(result)['prediction']
    for label in result:
        if label[1] >= SMOKING_THRESHOLD:
            labels.append([object_categories[int(label[0])],visualize_detection(label)])
    return labels

def detect_alcohol_classify(img):
    labels = []
    object_categories = [
        'alcohol_bottles',
        'wine_glasses',    
        'beer_mugs',
        'shots_glasses'
    ]
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    response = runtime.invoke_endpoint(
        EndpointName='alcohol',
        ContentType='application/x-image',
        Body=bytearray(img)
        )
    result = response['Body'].read().decode("utf-8")
    result = json.loads(result)['prediction']
    for label in result:
        if label[1] >= ALCOHOL_THRESHOLD:
            labels.append([object_categories[int(label[0])],visualize_detection(label)])
    return labels

def detect_fire_classify(img):
    labels = []
    object_categories = [
        'fire'
    ]
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    response = runtime.invoke_endpoint(
        EndpointName='fire',
        ContentType='application/x-image',
        Body=bytearray(img)
        )
    result = response['Body'].read().decode("utf-8")
    result = json.loads(result)['prediction']
    for label in result:
        if label[1] >= FIRE_THRESHOLD:
            labels.append([object_categories[int(label[0])],visualize_detection(label)])
    return labels

def detect_flag_classify(img):
    labels = []
    object_categories = [
        'indian_flag'
    ]
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    response = runtime.invoke_endpoint(
        EndpointName='flag',
        ContentType='application/x-image',
        Body=bytearray(img)
        )
    result = response['Body'].read().decode("utf-8")
    result = json.loads(result)['prediction']
    for label in result:
        if label[1] >= FLAG_THRESHOLD:
            labels.append([object_categories[int(label[0])],visualize_detection(label)])
    return labels

def detect_statue_classify(img):
    labels = []
    object_categories = [
        'naked statue'
    ]
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    response = runtime.invoke_endpoint(
        EndpointName='nakedstatue',
        ContentType='application/x-image',
        Body=bytearray(img)
        )
    result = response['Body'].read().decode("utf-8")
    result = json.loads(result)['prediction']
    for label in result:
        if label[1] >= STATUE_THRESHOLD:
            labels.append([object_categories[int(label[0])],visualize_detection(label)])
    return labels

def detect_sexdolls_classify(img):
    labels = []
    object_categories = [
        'sex dolls'
    ]
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    response = runtime.invoke_endpoint(
        EndpointName='sexdolls',
        ContentType='application/x-image',
        Body=bytearray(img)
        )
    result = response['Body'].read().decode("utf-8")
    result = json.loads(result)['prediction']
    for label in result:
        if label[1] >= SEXDOLLS_THRESHOLD:
            labels.append([object_categories[int(label[0])],visualize_detection(label)])
    return labels

def detect_drugs_classify(img):
    labels = []
    object_categories = ["Pills", "Needles", "Bong", "Snorting"]
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    response = runtime.invoke_endpoint(
        EndpointName='drugs',
        ContentType='application/x-image',
        Body=bytearray(img)
        )
    result = response['Body'].read().decode("utf-8")
    result = json.loads(result)['prediction']
    for label in result:
        if label[1] >= DRUGS_THRESHOLD:
            object_label = object_categories[int(label[0])]
            if object_label.upper() not in barred_detections:
                labels.append([object_label, visualize_detection(label)])
    return labels

def detect_complaince_video(img):
    runtime = boto3.Session().client(service_name='sagemaker-runtime', region_name='ap-south-1')
    object_categories = ['alcohol', 'blood', 'ciggarette', 'nudity', 'safe', 'weapon']
    response = runtime.invoke_endpoint(
        EndpointName='compliance',
        ContentType='application/x-image',
        Body=bytearray(img)
        )
    result = response['Body'].read().decode("utf-8")
    result = json.loads(result)
    pred_label_id = np.argmax(result)
    label, probability = object_categories[pred_label_id], result[pred_label_id]
    if label not in ['safe', 'nudity'] and probability >= COMPLIANCE_THRESHOLD:
        return label

@app.task(on_failure=failure_response)
def compliance_video_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_frame = myclip.get_frame(slot)

    j = PIL.Image.fromarray(current_frame)
    with io.BytesIO() as output:
        j.save(output, format="jpeg")
        contents = output.getvalue()
        detection = [x for x in (detect_complaince_video(contents), detect_nudity_classify(contents)) if x]
    for label,bbox in detection:
        x, y, width, height = bbox
        complaince_tag = GenericTag.objects.filter(title__iexact="Compliance").first()
        if not complaince_tag:
            complaince_tag = GenericTag.objects.create(title="Compliance", parent=None)
        complaince_tag_obj = GenericTag.objects.filter(title__iexact=label, parent=complaince_tag).first()
        if not complaince_tag_obj:
            complaince_tag_obj = GenericTag.objects.create(title=label, parent=complaince_tag)
        frame_tag_obj = FrameTag.objects.create(tag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id),
                                        frame_in=int((slot - JUMP) * (video_obj.frame_rate)),
                                        frame_out=int(slot * (video_obj.frame_rate)), words=label,
                                        up_left_x = x, up_left_y = y,
                                        width = width, height = height)
        frame_tag_obj.save()

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += ((JUMP/2) / video_obj.duration)
    auto_job.save()
    close_clip(myclip)


@app.task(on_failure=failure_response)
def drugs_video_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_frame = myclip.get_frame(slot)

    detection = []
    img_width, img_height = video_obj.width, video_obj.height
    j = PIL.Image.fromarray(current_frame)
    with io.BytesIO() as output:
        j.save(output, format="jpeg")
        contents = output.getvalue()
        detection = detect_drugs_classify(contents)

    if detection:
        imgURL = image_to_azure_url(j)
        correction_tag_obj = CorrectionTag.objects.create(video=get_object_or_404(Video, pk=video_id),
                                                          frame_in=int((slot - JUMP) * (video_obj.frame_rate)), image_url=imgURL,
                                                          frame_out=int(slot * (video_obj.frame_rate)))
        correction_tag_obj.save()
        print(detection)
        for label,bbox in detection:
            x, y, width, height = bbox
            complaince_tag = GenericTag.objects.filter(title__iexact="Drugs").first()
            if not complaince_tag:
                complaince_tag = GenericTag.objects.create(title="Drugs", parent=None)
            complaince_tag_obj = GenericTag.objects.filter(title__iexact=label, parent=complaince_tag).first()
            if not complaince_tag_obj:
                complaince_tag_obj = GenericTag.objects.create(title=label, parent=complaince_tag)
            frame_tag_obj = FrameTag.objects.create(tag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id),
                                            frame_in=int((slot - JUMP) * (video_obj.frame_rate)),
                                            frame_out=int(slot * (video_obj.frame_rate)), words=label,
                                            up_left_x = x, up_left_y = y,
                                            width = width, height = height, img_width = img_width, img_height = img_height)
            frame_tag_obj.save()
            check_tag_obj = CheckTag.objects.create(autotag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id), up_left_x = x, up_left_y = y,
                                                     width = width, height = height, img_width = img_width, img_height = img_height)
            check_tag_obj.save()
            correction_tag_obj.checktag.add(check_tag_obj)

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += ((JUMP/2) / video_obj.duration)
    auto_job.save()
    close_clip(myclip)

@app.task(on_failure=failure_response)
def smoke_video_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_frame = myclip.get_frame(slot)

    detection = []
    img_width, img_height = video_obj.width, video_obj.height
    j = PIL.Image.fromarray(current_frame)
    with io.BytesIO() as output:
        j.save(output, format="jpeg")
        contents = output.getvalue()
        detection = detect_smoke_classify(contents)

    if detection:
        imgURL = image_to_azure_url(j)
        correction_tag_obj = CorrectionTag.objects.create(video=get_object_or_404(Video, pk=video_id),
                                                          frame_in=int((slot - JUMP) * (video_obj.frame_rate)), image_url=imgURL,
                                                          frame_out=int(slot * (video_obj.frame_rate)))
        correction_tag_obj.save()
        print(detection)
        for label,bbox in detection:
            x, y, width, height = bbox
            complaince_tag = GenericTag.objects.filter(title__iexact="Smoking").first()
            if not complaince_tag:
                complaince_tag = GenericTag.objects.create(title="Smoking", parent=None)
            complaince_tag_obj = GenericTag.objects.filter(title__iexact=label, parent=complaince_tag).first()
            if not complaince_tag_obj:
                complaince_tag_obj = GenericTag.objects.create(title=label, parent=complaince_tag)
            frame_tag_obj = FrameTag.objects.create(tag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id),
                                            frame_in=int((slot - JUMP) * (video_obj.frame_rate)),
                                            frame_out=int(slot * (video_obj.frame_rate)), words=label,
                                            up_left_x = x, up_left_y = y,
                                            width = width, height = height, img_width = img_width, img_height = img_height)
            frame_tag_obj.save()
            check_tag_obj = CheckTag.objects.create(autotag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id), up_left_x = x, up_left_y = y,
                                                     width = width, height = height, img_width = img_width, img_height = img_height)
            check_tag_obj.save()
            correction_tag_obj.checktag.add(check_tag_obj)

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += ((JUMP/2) / video_obj.duration)
    auto_job.save()
    close_clip(myclip)

@app.task(on_failure=failure_response)
def alcohol_video_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_frame = myclip.get_frame(slot)

    detection = []
    img_width, img_height = video_obj.width, video_obj.height
    j = PIL.Image.fromarray(current_frame)
    with io.BytesIO() as output:
        j.save(output, format="jpeg")
        contents = output.getvalue()
        detection = detect_alcohol_classify(contents)
    if detection:
        print(detection)
        imgURL = image_to_azure_url(j)
        correction_tag_obj = CorrectionTag.objects.create(video=get_object_or_404(Video, pk=video_id),
                                                          frame_in=int((slot - JUMP) * (video_obj.frame_rate)), image_url=imgURL,
                                                          frame_out=int(slot * (video_obj.frame_rate)))
        correction_tag_obj.save()
        for label,bbox in detection:
            x, y, width, height = bbox
            complaince_tag = GenericTag.objects.filter(title__iexact="Alcohol").first()
            if not complaince_tag:
                complaince_tag = GenericTag.objects.create(title="Alcohol", parent=None)
            complaince_tag_obj = GenericTag.objects.filter(title__iexact=label, parent=complaince_tag).first()
            if not complaince_tag_obj:
                complaince_tag_obj = GenericTag.objects.create(title=label, parent=complaince_tag)
            frame_tag_obj = FrameTag.objects.create(tag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id),
                                            frame_in=int((slot - JUMP) * (video_obj.frame_rate)),
                                            frame_out=int(slot * (video_obj.frame_rate)), words=label,
                                        up_left_x = x, up_left_y = y,
                                        width = width, height = height, img_width = img_width, img_height = img_height)
            frame_tag_obj.save()
            check_tag_obj = CheckTag.objects.create(autotag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id), up_left_x = x, up_left_y = y,
                                                     width = width, height = height, img_width = img_width, img_height = img_height)
            check_tag_obj.save()
            correction_tag_obj.checktag.add(check_tag_obj)

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += ((JUMP/2) / video_obj.duration)
    auto_job.save()
    close_clip(myclip)

@app.task(on_failure=failure_response)
def fire_video_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_frame = myclip.get_frame(slot)

    detection = []
    img_width, img_height = video_obj.width, video_obj.height
    j = PIL.Image.fromarray(current_frame)
    with io.BytesIO() as output:
        j.save(output, format="jpeg")
        contents = output.getvalue()
        detection = detect_fire_classify(contents)
    if detection:
        print(detection)
        imgURL = image_to_azure_url(j)
        correction_tag_obj = CorrectionTag.objects.create(video=get_object_or_404(Video, pk=video_id),
                                                          frame_in=int((slot - JUMP) * (video_obj.frame_rate)), image_url=imgURL,
                                                          frame_out=int(slot * (video_obj.frame_rate)))
        correction_tag_obj.save()

        for label,bbox in detection:
            x, y, width, height = bbox
            complaince_tag = GenericTag.objects.filter(title__iexact="Fire").first()
            if not complaince_tag:
                complaince_tag = GenericTag.objects.create(title="Fire", parent=None)
            complaince_tag_obj = GenericTag.objects.filter(title__iexact=label, parent=complaince_tag).first()
            if not complaince_tag_obj:
                complaince_tag_obj = GenericTag.objects.create(title=label, parent=complaince_tag)
            frame_tag_obj = FrameTag.objects.create(tag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id),
                                            frame_in=int((slot - JUMP) * (video_obj.frame_rate)),
                                            frame_out=int(slot * (video_obj.frame_rate)), words=label,
                                        up_left_x = x, up_left_y = y,
                                        width = width, height = height, img_width = img_width, img_height = img_height)
            frame_tag_obj.save()
            check_tag_obj = CheckTag.objects.create(autotag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id), up_left_x = x, up_left_y = y,
                                                     width = width, height = height, img_width = img_width, img_height = img_height)
            check_tag_obj.save()
            correction_tag_obj.checktag.add(check_tag_obj)

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += ((JUMP/2) / video_obj.duration)
    auto_job.save()
    close_clip(myclip)

@app.task(on_failure=failure_response)
def sexdolls_video_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_frame = myclip.get_frame(slot)

    detection = []
    img_width, img_height = video_obj.width, video_obj.height
    j = PIL.Image.fromarray(current_frame)
    with io.BytesIO() as output:
        j.save(output, format="jpeg")
        contents = output.getvalue()
        detection = detect_sexdolls_classify(contents)
    if detection:
        print(detection)
        imgURL = image_to_azure_url(j)
        correction_tag_obj = CorrectionTag.objects.create(video=get_object_or_404(Video, pk=video_id),
                                                          frame_in=int((slot - JUMP) * (video_obj.frame_rate)), image_url=imgURL,
                                                          frame_out=int(slot * (video_obj.frame_rate)))
        correction_tag_obj.save()
        for label,bbox in detection:
            x, y, width, height = bbox
            complaince_tag = GenericTag.objects.filter(title__iexact="Sex Dolls").first()
            if not complaince_tag:
                complaince_tag = GenericTag.objects.create(title="Sex Dolls", parent=None)
            complaince_tag_obj = GenericTag.objects.filter(title__iexact=label, parent=complaince_tag).first()
            if not complaince_tag_obj:
                complaince_tag_obj = GenericTag.objects.create(title=label, parent=complaince_tag)
            frame_tag_obj = FrameTag.objects.create(tag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id),
                                            frame_in=int((slot - JUMP) * (video_obj.frame_rate)),
                                            frame_out=int(slot * (video_obj.frame_rate)), words=label,
                                        up_left_x = x, up_left_y = y,
                                        width = width, height = height, img_width = img_width, img_height = img_height)
            frame_tag_obj.save()
            check_tag_obj = CheckTag.objects.create(autotag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id), up_left_x = x, up_left_y = y,
                                                     width = width, height = height, img_width = img_width, img_height = img_height)
            check_tag_obj.save()
            correction_tag_obj.checktag.add(check_tag_obj)

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += ((JUMP/2) / video_obj.duration)
    auto_job.save()
    close_clip(myclip)

@app.task(on_failure=failure_response)
def flag_video_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_frame = myclip.get_frame(slot)

    detection = []
    img_width, img_height = video_obj.width, video_obj.height
    j = PIL.Image.fromarray(current_frame)
    with io.BytesIO() as output:
        j.save(output, format="jpeg")
        contents = output.getvalue()
        detection = detect_flag_classify(contents)

    if detection:
        print(detection)
        imgURL = image_to_azure_url(j)
        correction_tag_obj = CorrectionTag.objects.create(video=get_object_or_404(Video, pk=video_id),
                                                          frame_in=int((slot - JUMP) * (video_obj.frame_rate)), image_url=imgURL,
                                                          frame_out=int(slot * (video_obj.frame_rate)))
        correction_tag_obj.save()
        for label,bbox in detection:
            x, y, width, height,img_width, img_height = bbox
            complaince_tag = GenericTag.objects.filter(title__iexact="Indian Flag").first()
            if not complaince_tag:
                complaince_tag = GenericTag.objects.create(title="Indian Flag", parent=None)
            complaince_tag_obj = GenericTag.objects.filter(title__iexact=label, parent=complaince_tag).first()
            if not complaince_tag_obj:
                complaince_tag_obj = GenericTag.objects.create(title=label, parent=complaince_tag)
            frame_tag_obj = FrameTag.objects.create(tag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id),
                                            frame_in=int((slot - JUMP) * (video_obj.frame_rate)),
                                            frame_out=int(slot * (video_obj.frame_rate)), words=label,
                                        up_left_x = x, up_left_y = y,
                                        width = width, height = height, img_width = img_width, img_height = img_height)
            frame_tag_obj.save()
            check_tag_obj = CheckTag.objects.create(autotag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id), up_left_x = x, up_left_y = y,
                                                     width = width, height = height, img_width = img_width, img_height = img_height)
            check_tag_obj.save()
            correction_tag_obj.checktag.add(check_tag_obj)

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += ((JUMP/2) / video_obj.duration)
    auto_job.save()
    close_clip(myclip)

@app.task(on_failure=failure_response)
def statue_video_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_frame = myclip.get_frame(slot)

    detection = []
    img_width, img_height = video_obj.width, video_obj.height
    j = PIL.Image.fromarray(current_frame)
    with io.BytesIO() as output:
        j.save(output, format="jpeg")
        contents = output.getvalue()
        detection = detect_statue_classify(contents)
    if detection:
        print(detection)
        imgURL = image_to_azure_url(j)
        correction_tag_obj = CorrectionTag.objects.create(video=get_object_or_404(Video, pk=video_id),
                                                          frame_in=int((slot - JUMP) * (video_obj.frame_rate)), image_url=imgURL,
                                                          frame_out=int(slot * (video_obj.frame_rate)))
        correction_tag_obj.save()
        for label,bbox in detection:
            x, y, width, height = bbox
            complaince_tag = GenericTag.objects.filter(title__iexact="Naked Statue").first()
            if not complaince_tag:
                complaince_tag = GenericTag.objects.create(title="Naked Statue", parent=None)
            complaince_tag_obj = GenericTag.objects.filter(title__iexact=label, parent=complaince_tag).first()
            if not complaince_tag_obj:
                complaince_tag_obj = GenericTag.objects.create(title=label, parent=complaince_tag)
            frame_tag_obj = FrameTag.objects.create(tag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id),
                                            frame_in=int((slot - JUMP) * (video_obj.frame_rate)),
                                            frame_out=int(slot * (video_obj.frame_rate)), words=label,
                                        up_left_x = x, up_left_y = y,
                                        width = width, height = height, img_width = img_width, img_height = img_height)
            frame_tag_obj.save()
            check_tag_obj = CheckTag.objects.create(autotag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id), up_left_x = x, up_left_y = y,
                                                     width = width, height = height, img_width = img_width, img_height = img_height)
            check_tag_obj.save()
            correction_tag_obj.checktag.add(check_tag_obj)

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += ((JUMP/2) / video_obj.duration)
    auto_job.save()
    close_clip(myclip)

class skinDetector(object):

    #class constructor
    def __init__(self, imageName):
        self.image = imageName
        if self.image is None:
            print("IMAGE NOT FOUND")
            exit(1)                          
        self.HSV_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        self.YCbCr_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2YCR_CB)
        self.binary_mask_image = self.HSV_image
    
    #function to process the image and segment the skin using the HSV and YCbCr colorspaces, followed by the Watershed algorithm
    def find_skin(self):
        self.__color_segmentation()
        mask = self.__region_based_segmentation()
        return mask

    #Apply a threshold to an HSV and YCbCr images, the used values were based on current research papers along with some
    # empirical tests and visual evaluation
    def __color_segmentation(self):
        lower_HSV_values = np.array([0, 48, 80], dtype = "uint8")
        upper_HSV_values = np.array([20, 255, 255], dtype = "uint8")

        lower_YCbCr_values = np.array((0, 138, 67), dtype = "uint8")
        upper_YCbCr_values = np.array((255, 173, 133), dtype = "uint8")

        #A binary mask is returned. White pixels (255) represent pixels that fall into the upper/lower.
        mask_YCbCr = cv2.inRange(self.YCbCr_image, lower_YCbCr_values, upper_YCbCr_values)
        mask_HSV = cv2.inRange(self.HSV_image, lower_HSV_values, upper_HSV_values) 

        self.binary_mask_image = cv2.add(mask_HSV,mask_YCbCr)

    #Function that applies Watershed and morphological operations on the thresholded image
    def __region_based_segmentation(self):
        #morphological operations
        image_foreground = cv2.erode(self.binary_mask_image,None,iterations = 2)     	#remove noise
        dilated_binary_image = cv2.dilate(self.binary_mask_image,None,iterations = 4)   #The background region is reduced a little because of the dilate operation
        
        image_background = cv2.adaptiveThreshold(dilated_binary_image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
            cv2.THRESH_BINARY,11,2)
        _,image_background = cv2.threshold(image_background,1,128,cv2.ADAPTIVE_THRESH_GAUSSIAN_C)  #set all background regions to 128
        
        image_marker = cv2.add(image_foreground,image_background)   #add both foreground and backgroud, forming markers. The markers are "seeds" of the future image regions.
        image_marker32 = np.int32(image_marker) #convert to 32SC1 format

        cv2.watershed(self.image,image_marker32)
        m = cv2.convertScaleAbs(image_marker32) #convert back to uint8 

        #bitwise of the mask with the input image
        _,self.image_mask = cv2.threshold(m,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        _ = cv2.bitwise_and(self.image,self.image,mask = self.image_mask)
        
        return self.image_mask

def skin_percentage(img_file):
    detector = skinDetector(img_file)
    mask = detector.find_skin()
    _, counts = np.unique(mask, return_counts=True)
    return counts[1]/(counts[0]+counts[1])
    
@app.task(on_failure=failure_response)
def compliance_nudity_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_frame = myclip.get_frame(slot)
    open_cv_image = current_frame[:, :, ::-1].copy()
    j = PIL.Image.fromarray(current_frame)
    
    skin_percent = skin_percentage(open_cv_image)
    if skin_percent > 0.35 and skin_percent <0.99:
        detection = []
        img_width, img_height = video_obj.width, video_obj.height  
        with io.BytesIO() as output:
            j.save(output, format="jpeg")
            contents = output.getvalue()
            detection = detect_nudity_classify(contents)
        if detection:
            print(detection)
            imgURL = image_to_azure_url(j)
            correction_tag_obj = CorrectionTag.objects.create(video=get_object_or_404(Video, pk=video_id),
                                                              frame_in=int((slot - JUMP) * (video_obj.frame_rate)), image_url=imgURL,
                                                              frame_out=int(slot * (video_obj.frame_rate)))
            correction_tag_obj.save()
            for label,bbox in detection:
                x, y, width, height = bbox
                complaince_tag = GenericTag.objects.filter(title__iexact="Nudity").first()
                if not complaince_tag:
                    complaince_tag = GenericTag.objects.create(title="Nudity", parent=None)
                complaince_tag_obj = GenericTag.objects.filter(title__iexact=label, parent=complaince_tag).first()
                if not complaince_tag_obj:
                    complaince_tag_obj = GenericTag.objects.create(title=label, parent=complaince_tag)
                frame_tag_obj = FrameTag.objects.create(tag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id),
                                                frame_in=int((slot - JUMP) * (video_obj.frame_rate)),
                                                frame_out=int(slot * (video_obj.frame_rate)), words=label,
                                            up_left_x = x, up_left_y = y,
                                            width = width, height = height, img_width = img_width, img_height = img_height)
                frame_tag_obj.save()
                check_tag_obj = CheckTag.objects.create(autotag=complaince_tag_obj, video=get_object_or_404(Video, pk=video_id), up_left_x = x, up_left_y = y,
                                                         width = width, height = height, img_width = img_width, img_height = img_height)
                check_tag_obj.save()
                correction_tag_obj.checktag.add(check_tag_obj)

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += ((JUMP/2) / video_obj.duration)
    auto_job.save()
    close_clip(myclip)


@app.task(on_failure=failure_response)
def logo_video_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_frame = myclip.get_frame(slot)

    j = PIL.Image.fromarray(current_frame)
    with io.BytesIO() as output:
        j.save(output, format="jpeg")
        contents = output.getvalue()
        labels = detect_logo(contents)

    for label in labels:
        logo_tag = GenericTag.objects.filter(title__iexact="Logo").first()
        if not logo_tag:
            logo_tag = GenericTag.objects.create(title="Logo", parent=None)
        logo_tag_obj = GenericTag.objects.filter(title__iexact=label, parent=logo_tag).first()
        if not logo_tag_obj:
            logo_tag_obj = GenericTag.objects.create(title=label, parent=logo_tag)
        frame_tag_obj = FrameTag.objects.create(tag=logo_tag_obj, video=get_object_or_404(Video, pk=video_id),
                                        frame_in=int((slot - JUMP) * (video_obj.frame_rate)),
                                        frame_out=int(slot * (video_obj.frame_rate)), words=label)
        frame_tag_obj.save()

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += ((JUMP/2) / video_obj.duration)
    auto_job.save()
    close_clip(myclip)

@app.task(on_failure=failure_response)
def background_logo_video(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    tmp_file_name = save_video_local(input_file)
    #for st in range(1, int(video_obj.duration)):
    #    location_video_in_slot(st, tmp_file_name, video_id, auto_job.id)
    for st in np.arange(JUMP,float(video_obj.duration),JUMP):
        logo_video_in_slot(math.floor(st*10)/10, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    merge_object_detections.delay(video_id)
    silentremove(tmp_file_name)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()

@app.task(on_failure=failure_response)
def location_video_in_slot(slot, input_file, video_id, job_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_frame = myclip.get_frame(slot)

    j = PIL.Image.fromarray(current_frame)
    with io.BytesIO() as output:
        j.save(output, format="jpeg")
        contents = output.getvalue()
        labels = [x['class'] for x in detect_location(contents)]

    for label in labels[:1]:
        location_tag = GenericTag.objects.filter(title__iexact="Location").first()
        if not location_tag:
            location_tag = GenericTag.objects.create(title="Location", parent=None)
        location_tag_obj = GenericTag.objects.filter(title__iexact=label, parent=location_tag).first()
        if not location_tag_obj:
            location_tag_obj = GenericTag.objects.create(title=label, parent=location_tag)
        frame_tag_obj = FrameTag.objects.create(tag=location_tag_obj, video=get_object_or_404(Video, pk=video_id),
                                        frame_in=int((slot - JUMP) * (video_obj.frame_rate)),
                                        frame_out=int(slot * (video_obj.frame_rate)), words=label)
        frame_tag_obj.save()

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += ((JUMP/2) / video_obj.duration)
    auto_job.save()
    close_clip(myclip)

@app.task(on_failure=failure_response)
def background_location_video(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    tmp_file_name = save_video_local(input_file)
    #for st in range(1, int(video_obj.duration)):
    #    location_video_in_slot(st, tmp_file_name, video_id, auto_job.id)
    for st in np.arange(JUMP,float(video_obj.duration),JUMP):
        location_video_in_slot(math.floor(st*10)/10, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    merge_object_detections.delay(video_id)
    silentremove(tmp_file_name)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()
    index_locations_tessact.delay(video_id)

@app.task(on_failure=failure_response)
def background_compliance_video(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    tmp_file_name = save_video_local(input_file)
    #for st in range(1, int(video_obj.duration)):
    #    compliance_video_in_slot(st, tmp_file_name, video_id, auto_job.id)
    for st in np.arange(JUMP,float(video_obj.duration),JUMP):
        compliance_video_in_slot(math.floor(st*10)/10, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    merge_object_detections.delay(video_id)
    silentremove(tmp_file_name)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()

@app.task(on_failure=failure_response)
def background_nudity_video(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    tmp_file_name = save_video_local(input_file)
    #for st in range(1, int(video_obj.duration)):
    #    compliance_video_in_slot(st, tmp_file_name, video_id, auto_job.id)
    for st in np.arange(JUMP,float(video_obj.duration),JUMP):
        compliance_nudity_in_slot(math.floor(st*10)/10, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    merge_object_detections.delay(video_id)
    silentremove(tmp_file_name)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()

@app.task(on_failure=failure_response)
def background_smoke_video(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    tmp_file_name = save_video_local(input_file)

    for st in np.arange(JUMP,float(video_obj.duration),JUMP):
        smoke_video_in_slot(math.floor(st*10)/10, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    merge_object_detections.delay(video_id)
    silentremove(tmp_file_name)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()

@app.task(on_failure=failure_response)
def background_drugs_video(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    tmp_file_name = save_video_local(input_file)
    #for st in range(1, int(video_obj.duration)):
    #    compliance_video_in_slot(st, tmp_file_name, video_id, auto_job.id)
    for st in np.arange(JUMP,float(video_obj.duration),JUMP):
        drugs_video_in_slot(math.floor(st*10)/10, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    merge_object_detections.delay(video_id)
    silentremove(tmp_file_name)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()

@app.task(on_failure=failure_response)
def background_alcohol_video(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    tmp_file_name = save_video_local(input_file)
    #for st in range(1, int(video_obj.duration)):
    #    compliance_video_in_slot(st, tmp_file_name, video_id, auto_job.id)
    for st in np.arange(JUMP,float(video_obj.duration),JUMP):
        alcohol_video_in_slot(math.floor(st*10)/10, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    merge_object_detections.delay(video_id)
    silentremove(tmp_file_name)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()

@app.task(on_failure=failure_response)
def background_fire_video(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    tmp_file_name = save_video_local(input_file)
    #for st in range(1, int(video_obj.duration)):
    #    compliance_video_in_slot(st, tmp_file_name, video_id, auto_job.id)
    for st in np.arange(JUMP,float(video_obj.duration),JUMP):
        fire_video_in_slot(math.floor(st*10)/10, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    merge_object_detections.delay(video_id)
    silentremove(tmp_file_name)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()

@app.task(on_failure=failure_response)
def background_sexdolls_video(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    tmp_file_name = save_video_local(input_file)
    #for st in range(1, int(video_obj.duration)):
    #    compliance_video_in_slot(st, tmp_file_name, video_id, auto_job.id)
    for st in np.arange(JUMP,float(video_obj.duration),JUMP):
        sexdolls_video_in_slot(math.floor(st*10)/10, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    merge_object_detections.delay(video_id)
    silentremove(tmp_file_name)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()

@app.task(on_failure=failure_response)
def background_flag_video(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    tmp_file_name = save_video_local(input_file)
    #for st in range(1, int(video_obj.duration)):
    #    compliance_video_in_slot(st, tmp_file_name, video_id, auto_job.id)
    for st in np.arange(JUMP,float(video_obj.duration),JUMP):
        flag_video_in_slot(math.floor(st*10)/10, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    # merge_object_detections.delay(video_id)
    silentremove(tmp_file_name)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()

@app.task(on_failure=failure_response)
def background_statue_video(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)
    tmp_file_name = save_video_local(input_file)
    #for st in range(1, int(video_obj.duration)):
    #    compliance_video_in_slot(st, tmp_file_name, video_id, auto_job.id)
    for st in np.arange(JUMP,float(video_obj.duration),JUMP):
        statue_video_in_slot(math.floor(st*10)/10, tmp_file_name, video_id, auto_job.id)
    chord_clean_video_file.delay(tmp_file_name, job_id)
    merge_object_detections.delay(video_id)
    silentremove(tmp_file_name)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()

@app.task(on_failure=failure_response)
def background_compliance_audio(input_file, video_id, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    local_video_file = save_video_local(input_file)
    audio_file = create_audio(local_video_file)
    video_title = Video.objects.filter(id=video_id).first().title
    video_fps = int(Video.objects.filter(id=video_id).first().frame_rate)
    language = AssetVersion.objects.filter(video_id=video_id).first().language
    lang = 'en-US'
    if language:
        if language.name == 'Hindi':
            lang = 'hi-IN'
    subtitles = fetch_subtitles(video_title)
    if subtitles:
        process_for_gentle(audio_file, subtitles, video_fps, video_id)
    else:
        break_audio_complaince(audio_file, '/tmp/audio/', 10, video_id, lang)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta = auto_job.eta + 0.5
    if auto_job.eta >= 1:
        auto_job.job_status = 'PRD'
    auto_job.save()

def break_audio_complaince(input_file, tmp_folder, step, video_id, lang="en-US"):
    command = [FFPROBE_BIN,
               '-v', 'quiet',
               '-print_format', 'json',
               '-show_format',
               '-show_streams',
               input_file]
    output = sp.check_output(command)
    output = output.decode('utf-8')
    metadata_output = json.loads(output)
    duration = metadata_output['streams'][0]['duration']
    sample_rate = metadata_output['streams'][0]['sample_rate']
    max_min = int(math.ceil(float(duration) / step))
    video_obj = Video.objects.filter(id=video_id).first()
    fps = int(video_obj.frame_rate)
    # print(max_min)
    data = {}
    start_time = time.time()
    last_time = start_time
    client = language.LanguageServiceClient()
    with codecs.open("./utils/foul.txt", 'r', encoding='utf-8') as fd:
        filter_list = list(set([f.strip() for f in fd.readlines()]))
    profanity_tag = Tag.objects.filter(name__iexact="Profanity").first()
    if not profanity_tag:
        profanity_tag = Tag.objects.create(name="Profanity")
        complaince_tag = TagCategory.objects.filter(name__iexact="Compliance").first()
        if not complaince_tag:
            complaince_tag = TagCategory.objects.create(name="Compliance")
        profanity_tag.category = complaince_tag
        profanity_tag.save()
    for i in range(max_min):
        print("index : {}".format(i))

        file_name = os.path.join(tmp_folder, 'tmp.wav')
        check_or_create_file(file_name)
        start_t = i * step -1 if i*step -1 >=0 else 0
        command = [FFMPEG_BIN,
                   '-v', 'quiet',
                   '-ss', str(start_t),
                   '-i', input_file,
                   '-t', str(step+2),
                   '-ac', '1',
                   '-acodec', 'pcm_s16le', '-ar', '16000',
                   file_name, '-y']

        output = sp.check_output(command)
        current_time = time.time()

        data_trans, word_level = print_subs(file_name, lang, 16000)

        if data_trans:
            worddic = word_level['words']
            for dic in worddic:
                if dic['word'].strip() in filter_list:
                    stime = i*fps*step +  ((dic['start_time'] - 1) * fps)
                    etime = i*fps*step  + ((dic['end_time'] + 1) * fps)
                    if lang == 'hi-IN':
                        keyword_tag = KeywordTag.objects.create(video=video_obj, words=hindi_foul_words_dic[dic['word']],
                                        frame_in=stime, frame_out=etime, sentiment_score=0,
                                        sentiment_magnitude=0, word_level=json.dumps(word_level))
                    else:
                        keyword_tag = KeywordTag.objects.create(video=video_obj, words=dic['word'],
                                        frame_in=stime, frame_out=etime, sentiment_score=0,
                                        sentiment_magnitude=0, word_level=json.dumps(word_level))
                    keyword_tag.tags.add(profanity_tag)
                    keyword_tag.save()

        data[str(i)] = data_trans
        print("Time elapsed %g" % (current_time - last_time))
        last_time = current_time
    silentremove(input_file)

def process_for_gentle(audio_file, subtitles, fps, video_id):
    subtitle_file = file_name = os.path.join('/tmp/', str(uuid.uuid4()) + '.txt')
    subtitle_file_obj = open(subtitle_file, 'w')
    subtitle_file_obj.writelines(subtitles)
    subtitle_file_obj.close()
    video_obj = Video.objects.filter(id=video_id).first()
    params = (('async', 'false'),)
    files = {'audio': (audio_file, open(audio_file, 'rb')),
            'transcript': (subtitle_file, open(subtitle_file, 'rb')),}

    response = requests.post('http://gentle:8765/transcriptions', params=params, files=files)
    data = response.json()['words']
    silentremove(audio_file)
    silentremove(subtitle_file)
    foul_list = list(set([x.replace("\n", '').strip().lower() for x in open('./utils/foul.txt').readlines() if x != '\n' ]))
    profanity_tag = Tag.objects.filter(name__iexact="Profanity").first()
    if not profanity_tag:
        profanity_tag = Tag.objects.create(name="Profanity")
        complaince_tag = TagCategory.objects.filter(name__iexact="Compliance").first()
        if not complaince_tag:
            complaince_tag = TagCategory.objects.create(name="Compliance")
        profanity_tag.category = profanity_tag
        profanity_tag.save()
    for each in data:
        if each['case'] == 'success':
            if each['word'].lower() in foul_list:
                keyword_tag = KeywordTag.objects.create(video=video_obj, words=each['word'].lower(),
                                    frame_in=(each['start']*fps)-10, frame_out=each['end'] * fps, sentiment_score=0,
                                    sentiment_magnitude=0, word_level=json.dumps({}))
                keyword_tag.tags.add(profanity_tag)
                keyword_tag.save()


@app.task(on_failure=failure_response)
def background_video_processing_hardcuts(input_file, video_id, job_id, tmp_file_name):
    print(input_file)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    # tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4()) + '.mp4')
    print(tmp_file_name)
    check_or_create_file(tmp_file_name)
    # urlretrieve(input_file, tmp_file_name)
    with requests.get(input_file, stream=True) as r:
        with open(tmp_file_name, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    slots = get_cuts(tmp_file_name)
    video_obj = get_object_or_404(Video, pk=video_id)
    silentremove(tmp_file_name)
    try:
        hardcuts_obj = video_obj.hardcuts
        hardcuts_obj.cuts = slots
    except ObjectDoesNotExist:
        hardcuts_obj = HardCuts.objects.create(cuts=slots, video=get_object_or_404(Video, pk=video_id))
    auto_job.eta = 1.0
    auto_job.job_status = 'PRD'
    auto_job.save()
    hardcuts_obj.save()


@app.task
def set_hardcuts(input_file, video_id):
    tmp_file_name = save_video_local(input_file)
    slots = get_cuts(tmp_file_name)
    video_obj = get_object_or_404(Video, pk=video_id)
    silentremove(tmp_file_name)
    try:
        hardcuts_obj = video_obj.hardcuts
        hardcuts_obj.cuts = slots
    except ObjectDoesNotExist:
        hardcuts_obj = HardCuts.objects.create(cuts=slots, video=get_object_or_404(Video, pk=video_id))
    hardcuts_obj.save()



@app.task
def detect_faces_in_slot(slot, input_file, video_id, job_id):
    face_ids = []

    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_time = slot -1
    slot_time = (random.random() * (slot - current_time) + current_time)
    frame_data = myclip.get_frame(slot_time)
    j = PIL.Image.fromarray(frame_data)
    imgURL = image_to_azure_url(j)
    new_frame = Frames.objects.create(file=imgURL)
    new_frame.save()
    video_frame = VideoFrame.objects.create(frame=new_frame, video=get_object_or_404(Video, pk=video_id), time=slot_time)
    video_frame.save()
    try:
        facesDetected = CF.face.detect(imgURL, attributes='emotion')
    except CF.util.CognitiveFaceException:
        return []
    face_tag,_ = Tag.objects.get_or_create(name='face')
    for face in facesDetected:
        face_ids.append(face['faceId'])
        top = face['faceRectangle']['top']
        left = face['faceRectangle']['left']
        width = face['faceRectangle']['width']
        height = face['faceRectangle']['height']
        emotion_final = "neutral"
        try:
            emotion = face["faceAttributes"]['emotion']
            emotion_q = 0
            emotion_final = None
            for e in emotion:
                if emotion[e] > emotion_q:
                    emotion_final = e
                    emotion_q = emotion[e]
        except KeyError:
            emotion_final = "neutral"

        faceRectObj = Rect.objects.create(x=left, y=top, w=width, h=height, frame=new_frame)
        faceRectObj.tags.add(face_tag.id)
        faceRectObj.save()

        faceImg = j.crop((left, top, left + width, top + height))
        imgURL = image_to_azure_url(faceImg)
        face_obj = Face.objects.create(azure_face_id=face['faceId'], face_img_url=imgURL, face_rect=faceRectObj, emotion=emotion_final)
        face_obj.save()
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += (1/video_obj.duration)
    auto_job.save()
    print("slot {}/{} done".format(slot, video_obj.duration))
    close_clip(myclip)
    return face_ids


def segment_similar_faces(similar_faces, video_obj):
    for faceGroup in similar_faces['groups']:
        fg = FaceGroup.objects.create(video=video_obj)
        fg.save()
        # vfg = VideoFaceGroup.objects.create(video=video_obj, face_group=fg)
        # vfg.save()
        for face in faceGroup:
            face_obj = get_object_or_404(Face, azure_face_id=face)
            face_obj.face_group = fg
            face_obj.save()
        fg.set_time_line()
    try:
        for faceGroup in similar_faces['groups']:
            pg = PersonGroup.objects.get_or_create(title='People Now')
            result = CF.face.identify([faceGroup[0]], str(pg.id))
            candidates = result[0]['candidates']
            if len(candidates) > 0:
                ci = CloudPerson.objects.get(cloud_id=result[0]['candidates'][0]['personId'])
                fg.person = ci.person
                fg.save()
    except Exception as e:
        pass


@app.task
def face_matching(faceids, video_id, job_id, tmp_file_name):
    print("Face Matching started")
    video_obj = get_object_or_404(Video, pk=video_id)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    face_ids = []
    for f in faceids:
        face_ids += f
    if len(face_ids) > 1000:
        n = int(math.ceil(len(face_ids)/1000))
        for n_m in range(n):
            t_1 = n_m*1000
            t_2 = (n_m+1)*1000 if (n_m+1)*1000 < len(face_ids) else len(face_ids)
            try:
                similar_faces = CF.face.group(face_ids[t_1:t_2])
                segment_similar_faces(similar_faces, video_obj)
            except CF.util.CognitiveFaceException:
                pass
    else:
        try:
            similar_faces = CF.face.group(face_ids)
            segment_similar_faces(similar_faces, video_obj)
        except CF.util.CognitiveFaceException:
            auto_job.job_status = 'FAI'
            auto_job.eta = 1.0
            auto_job.save()
            silentremove(tmp_file_name)
            return False
    auto_job.job_status = 'PRD'
    auto_job.eta = 1.0
    auto_job.save()
    silentremove(tmp_file_name)
    # backgroudprocess_match_face.delay(video_id)
    time.sleep(15)
    print("Done check for PRD")

@app.task(on_failure=failure_response)
def background_video_processing_face_detection(input_file, video_id, job_id, tmp_file_name):
    print(input_file)
    print(tmp_file_name)
    check_or_create_file(tmp_file_name)
    # urlretrieve(input_file, tmp_file_name)
    with requests.get(input_file, stream=True) as r:
        with open(tmp_file_name, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    video_obj = get_object_or_404(Video, pk=video_id)
    face_groups = FaceGroup.objects.all().filter(video=video_obj)
    for face_group in face_groups:
        face_group.video = None
        face_group.save()
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    # chord is used because no task should wait for another task to complete
    res = chord((detect_faces_in_slot.s(st, tmp_file_name, video_id, auto_job.id) for st in range(1, int(video_obj.duration))), face_matching.s(video_id, job_id, tmp_file_name))
    res.apply_async()


def img2base64(img_link):
  with open("/tmp/img_file.jpg", "wb") as f:
      f.write()
  tmp_img = np.asarray(Image.open("/tmp/img_file.jpg"))
  tmp_thumb = tmp_img.resize((250, 250), Image.ANTIALIAS)
  tmp_thumb.save("/tmp/thumb_file.jpg")
  with open("/tmp/thumb_file.jpg", "rb") as img:
    thumb_string = base64.b64encode(img.read())
  # base64out = "data:image/jpeg;base64," + str(thumb_string)[2:-1]
  return(thumb_string)

def failure_response_match_face(self, exc, task_id, args, kwargs, einfo):
    print(args)
    print(kwargs)
    print("failed")
    #get job id
    job_id = str(args[1])
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'FAI'
    auto_job.eta = 1.0
    auto_job.save()

@app.task(on_failure=failure_response_match_face)
def backgroudprocess_match_face(video_id, job_id=None):
    video_obj = get_object_or_404(Video, pk=video_id)
    faceGroups = FaceGroup.objects.filter(video=video_obj)
    pg = PersonGroup.objects.get(title='People Now')
    if job_id:
        auto_job = AutoVideoJob.objects.get(id=job_id)
        auto_job.job_status = 'PRO'
        auto_job.eta = 0
        auto_job.save()
    eta_count = 0
    for faceGroup in faceGroups:
        if job_id:
            auto_job.eta = eta_count / len(faceGroups)
            auto_job.save()
        eta_count += 1
        count = 0
        print(str(faceGroup.id))
        hit = False
        for face in Face.objects.filter(face_group=faceGroup):
            # result = CF.face.identify([face.azure_face_id], str(pg.id))
            img_link = face.face_img_url
            result = CF.face.identify([face.azure_face_id], str(pg.id))
            candidates = result[0]['candidates']
            if len(candidates) > 0:
                ci = CloudPerson.objects.get(cloud_id=result[0]['candidates'][0]['personId'])
                faceGroup.person = ci.person
                faceGroup.save()
                hit=True
            output = urllib.request.urlopen(img_link).read()
            count += 1
            if hit or count>20:
                print(count)
                break

    if job_id:
        auto_job.job_status = 'PRD'
        auto_job.eta = 1.0
        auto_job.save()

def print_subs(file_name, lang, sample_rate):
    data = []
    word_level = {"words": []}
    # Loads the audio into memory
    with io.open(file_name, 'rb') as audio_file:
        content = audio_file.read()
        audio = types.RecognitionAudio(content=content)

    # Instantiates a client
    client = speech.SpeechClient()

    # Detects speech in the audio file
    try:
        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=lang,
            enable_word_time_offsets=True)

        # Detects speech in the audio file
        response = client.recognize(config, audio)
        if response.results:

            for result in response.results:
                alternatives = result.alternatives

                for alternative in alternatives:
                    data.append(alternative.transcript)

                    for word_info in alternative.words:
                        word = word_info.word
                        start_time = word_info.start_time
                        end_time = word_info.end_time
                        word_level["words"].append(
                            {
                                "word": word,
                                "start_time": start_time.seconds + start_time.nanos * 1e-9,
                                "end_time": end_time.seconds + end_time.nanos * 1e-9

                            }
                        )
                    break
    except Exception as e:
        print(e)
        pass
    return data, word_level

def translate_text(source, target, text):
    """Translates text into the target language.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """
    translate_client = translate.Client()

    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(
        text, target_language=target, source_language=source)
    return result['translatedText']


def get_stt_key():
    import http.client

    conn = http.client.HTTPSConnection("api.cognitive.microsoft.com")

    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'content-length': "0",
        'ocp-apim-subscription-key': "a18af4336c8948d7981b0c2228122fe1",
        'cache-control': "no-cache",
        'postman-token': "2dc2d903-e642-307a-ca58-6acaa829e14f"
    }

    conn.request("POST", "/sts/v1.0/issueToken", headers=headers)

    res = conn.getresponse()
    data = res.read()

    # print(data.decode("utf-8"))
    return data.decode("utf-8")


def get_stt_azure(file, lang):
    token = get_stt_key()
    # print(file)
    url = "https://speech.platform.bing.com/speech/recognition/interactive/cognitiveservices/v1?{}".format(urlencode({
        "language": lang,
        "profanity": "masked",
        "format": "detailed",
        "requestid": uuid.uuid4(),
    }))
    with open(file, 'rb') as fd:
        wav_data = fd.read()
        if sys.version_info >= (
        3, 6):  # chunked-transfer requests are only supported in the standard library as of Python 3.6+, use it if possible
            request = Request(url, data=fd, headers={
                "Authorization": "Bearer {}".format(token),
                "Content-type": "audio/wav; codec=\"audio/pcm\"; samplerate=16000",
                "Transfer-Encoding": "chunked",
            })
        else:  # fall back on manually formatting the POST body as a chunked request
            ascii_hex_data_length = "{:X}".format(len(wav_data)).encode("utf-8")
            chunked_transfer_encoding_data = ascii_hex_data_length + b"\r\n" + wav_data + b"\r\n0\r\n\r\n"
            request = Request(url, data=chunked_transfer_encoding_data, headers={
                "Authorization": "Bearer {}".format(token),
                "Content-type": "audio/wav; codec=\"audio/pcm\"; samplerate=16000",
                "Transfer-Encoding": "chunked",
            })

        try:
            response = urlopen(request, timeout=90)
        except HTTPError as e:
            raise RequestError("recognition request failed: {}".format(e.reason))
        except URLError as e:
            raise RequestError("recognition connection failed: {}".format(e.reason))
        response_text = response.read().decode("utf-8")
        result = json.loads(response_text)
        print(result)
        return result


def custom_stt_key():
    import http.client

    conn = http.client.HTTPSConnection("westus.api.cognitive.microsoft.com")

    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'content-length': "0",
        'ocp-apim-subscription-key': "0eac686db1934cfa8475a3678dde0606",
        'cache-control': "no-cache",
        'postman-token': "2dc2d903-e642-307a-ca58-6acaa829e14f"
    }

    conn.request("POST", "/sts/v1.0/issueToken", headers=headers)

    res = conn.getresponse()
    data = res.read()

    # print(data.decode("utf-8"))
    return data.decode("utf-8")


def custom_stt_azure(file):
    token = custom_stt_key()
    # print(token)
    # print(file)
    # url = "https://speech.platform.bing.com/speech/recognition/interactive/cognitiveservices/v1?{}".format(urlencode({
    #     "language": "en-US",
    #     "locale": "en-US",
    #     "requestid": uuid.uuid4(),
    # }))
    url = "https://159a6e251a634a21bb31d47ed68f8680.api.cris.ai/speech/recognition/interactive/cognitiveservices/v1?{}".format(urlencode({
        "language": "en-US",
        "locale": "en-US",
        "requestid": uuid.uuid4(),
    }))
    with open(file, 'rb') as fd:
        wav_data = fd.read()
        if sys.version_info >= (
                3,
                6):  # chunked-transfer requests are only supported in the standard library as of Python 3.6+, use it if possible
            request = Request(url, data=fd, headers={
                "Authorization": "Bearer {}".format(token),
                "Content-type": "audio/wav; codec=\"audio/pcm\"; samplerate=16000",
                "Transfer-Encoding": "chunked",
            })
        else:  # fall back on manually formatting the POST body as a chunked request
            ascii_hex_data_length = "{:X}".format(len(wav_data)).encode("utf-8")
            chunked_transfer_encoding_data = ascii_hex_data_length + b"\r\n" + wav_data + b"\r\n0\r\n\r\n"
            request = Request(url, data=chunked_transfer_encoding_data, headers={
                "Authorization": "Bearer {}".format(token),
                "Content-type": "audio/wav; codec=\"audio/pcm\"; samplerate=16000",
                "Transfer-Encoding": "chunked",
            })

        try:
            response = urlopen(request, timeout=90)
        except HTTPError as e:
            raise RequestError("recognition request failed: {}".format(e.reason))
        except URLError as e:
            raise RequestError("recognition connection failed: {}".format(e.reason))
        response_text = response.read().decode("utf-8")
        print("response text")
        print(response_text)
        result = json.loads(response_text)
        print("result")
        print(result)
        # print(result)
        return result


def break_audio(input_file, tmp_folder, lang, step, video_id, job_id):
    """
    :param input_file: audio file to be processed
    :param step: step duration
    :param tmp_folder: tmp folder path
    :param lang: number of parts to be created from the input file
    :param job_id: auto video job id for update
    :param video_id: to create KeywordTag
    :return:
    """
    command = [FFPROBE_BIN,
               '-v', 'quiet',
               '-print_format', 'json',
               '-show_format',
               '-show_streams',
               input_file]
    output = sp.check_output(command)
    output = output.decode('utf-8')
    metadata_output = json.loads(output)
    # print(metadata_output)
    duration = metadata_output['streams'][0]['duration']
    sample_rate = metadata_output['streams'][0]['sample_rate']

    print("duration : " + duration + " seconds")
    print("sample_rate : " + sample_rate)
    max_min = int(math.ceil(float(duration) / step))
    # print(max_min)
    data = {}
    start_time = time.time()
    last_time = start_time
    auto_job = AutoVideoJob.objects.get(id=job_id)
    video_obj = get_object_or_404(Video, pk=video_id)
    client = language.LanguageServiceClient()

    for i in range(max_min):
        auto_job.eta = i/max_min
        auto_job.save()
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("index : {}".format(i))

        file_name = os.path.join(tmp_folder, 'tmp.wav')
        check_or_create_file(file_name)
        start_t = i * step -1 if i*step -1 >=0 else 0
        command = [FFMPEG_BIN,
                   '-v', 'quiet',
                   '-ss', str(start_t),
                   '-i', input_file,
                   '-t', str(step+2),
                   '-ac', '1',
                   '-acodec', 'pcm_s16le', '-ar', '16000',
                   file_name, '-y']

        output = sp.check_output(command)
        current_time = time.time()
        # try:
        #     result = get_stt_azure(file_name, lang)
        #
        #     if result['RecognitionStatus'] == 'Success':
        #         nbest = result['NBest']
        #
        #         for tr in nbest:
        #             display = tr['ITN']
        #             masked_itn = tr['MaskedITN']
        #             if masked_itn != display or "en" not in lang:
        #
        #                 keyword_tag = KeywordTag.objects.create(video=video_obj, words=display,
        #                                                         frame_in=i*video_obj.frame_rate*step, frame_out=(i+1)*step*video_obj.frame_rate, sentiment_score=0,
        #                                                         sentiment_magnitude=0)
        #                 keyword_tag.save()
        #                 break
        # except RequestError:
        #     pass

        data_trans, word_level = print_subs(file_name, lang, 16000)

        if data_trans:
            text = "".join(data_trans)

            keyword_tag = KeywordTag.objects.create(video=video_obj, words=text,
                                                    frame_in=i*video_obj.frame_rate*step, frame_out=(i+1)*step*video_obj.frame_rate, sentiment_score=0,
                                                    sentiment_magnitude=0, word_level=word_level)
            keyword_tag.save()
        data[str(i)] = data_trans
        print("Time elapsed %g" % (current_time - last_time))
        last_time = current_time


def transcribe_gcs(gcs_uri, sample_rate):
    """Asynchronously transcribes the audio file specified by the gcs_uri."""
    from google.cloud import speech
    from google.cloud.speech import enums, types
    client = speech.SpeechClient()

    audio = types.RecognitionAudio(uri=gcs_uri)
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=int(sample_rate),
        language_code='en-US',
        enable_word_time_offsets=True)
    print("request sent")
    operation = client.long_running_recognize(config, audio)

    print('Waiting for operation to complete...')
    response = operation.result(timeout=900)

    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    word_list = []
    tmp_word = " "
    for result in response.results:
        # The first alternative is the most likely one for this portion.
        alternative = result.alternatives[0]
        print('Transcript: {}'.format(result.alternatives[0].transcript))
        print('Confidence: {}'.format(result.alternatives[0].confidence))

        for word_info in alternative.words:
            word = word_info.word
            start_time = word_info.start_time
            end_time = word_info.end_time
            start_time_fl = start_time.seconds + start_time.nanos * 1e-9
            end_time_fl = end_time.seconds + end_time.nanos * 1e-9
            print('Word: {}, start_time: {}, end_time: {}'.format(
                word,
                start_time.seconds + start_time.nanos * 1e-9,
                end_time.seconds + end_time.nanos * 1e-9))


# def long_running_stt(input_file):
#     command = [FFPROBE_BIN,
#                '-v', 'quiet',
#                '-print_format', 'json',
#                '-show_format',
#                '-show_streams',
#                input_file]
#     output = sp.check_output(command)
#     output = output.decode('utf-8')
#     metadata_output = json.loads(output)
#     # print(metadata_output)
#     duration = metadata_output['streams'][0]['duration']
#     sample_rate = metadata_output['streams'][0]['sample_rate']
#
#     print("duration : " + duration + " seconds")
#     print("sample_rate : " + sample_rate)
#     client = storage.Client()
#     file_name = input_file.split('/')[-1]
#     try:
#         bucket = client.get_bucket('new-trigger-test-media')
#         blob = bucket.blob(file_name)
#         with open(input_file, 'rb') as my_file:
#             blob.upload_from_file(my_file)
#
#         gs_url = "gs://new-trigger-test-media/"+file_name
#         print(gs_url)
#         transcribe_gcs(gs_url, sample_rate)
#     except exceptions.NotFound:
#         print('Sorry, that bucket does not exist!')

@app.task(on_failure=failure_response)
def backgroundprocess_keywords(input_file, video_id, job_id=None, language="en-IN", tmp_file_name=None):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    # delete all the old keyword tags
    video_obj = get_object_or_404(Video, pk=video_id)
    keywords = KeywordTag.objects.all().filter(video=video_obj)
    for keyword in keywords:
        keyword.delete()
    # get the video and audio
    print(input_file)
    # tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4()) + '.mp4')
    print(tmp_file_name)
    check_or_create_file(tmp_file_name)
    # urlretrieve(input_file, tmp_file_name)
    with requests.get(input_file, stream=True) as r:
        with open(tmp_file_name, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    output_audio_file = os.path.join("/tmp/audio/", str(uuid.uuid4()) + '.flac')
    check_or_create_file(output_audio_file)
    command = [FFMPEG_BIN,
               # '-v', 'quiet',
               '-i', tmp_file_name,
               # '-codec:a', 'libmp3lame',
               # '-qscale:a', '2',
               '-ac', '1',
               output_audio_file]
    output = sp.check_output(command)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    # process audio for sentences
    # long_running_stt(output_audio_file)
    break_audio(output_audio_file, '/tmp/audio/', language, 10, video_id, job_id)

    # create Keyword and save for the sentences
    auto_job.job_status = 'PRD'
    auto_job.eta = 1.0
    auto_job.save()
    silentremove(tmp_file_name)
    silentremove(output_audio_file)
    index_stt.delay(video_id)


def detect_text(content, lang="en"):
    """Detects text in the file."""
    base64_bytes = base64.b64encode(content)

    # third: decode these bytes to text
    # result: string (in utf-8)
    base64_string = base64_bytes.decode('utf-8')

    request = {
        'image': {
            "content": base64_string
        },
        'features': [{'type': vision.enums.Feature.Type.DOCUMENT_TEXT_DETECTION}],
        'imageContext': {
            "languageHints": [
                lang
            ]
        }

    }
    r = requests.post("https://vision.googleapis.com/v1/images:annotate?key=AIzaSyCfSAsgK_3Fm2s4a2_tYrXpKj0AZOD_oDM",
                      data=json.dumps(
                          {
                              "requests": [
                                  request
                              ]
                          }
                      ))
    response = r.json()
    try:
        texts = response['responses'][0]['textAnnotations']
        print('Texts:')
        words = []
        for text in texts:
            print('{} '.format(text['description']))
            words.append(text['description'])
        return words
    except KeyError:
        return ["-"]


@app.task
def detect_text_in_slot(slot, input_file, video_id, job_id, lang, add_sentiment):
    video_obj = get_object_or_404(Video, pk=video_id)
    myclip = VideoFileClip(input_file)
    current_time = slot -1
    slot_time = current_time / 5
    next_frame = myclip.get_frame(slot_time)
    current_frame = myclip.get_frame(slot/5)
    hist_1, _ = np.histogram(current_frame.ravel(), bins=32)
    hist_2, _ = np.histogram(next_frame.ravel(), bins=32)
    mean = np.mean(np.absolute(hist_2 - hist_1))
    if mean<10000:
        j = PIL.Image.fromarray(current_frame)
        with io.BytesIO() as output:
            j.save(output, format="PNG")
            contents = output.getvalue()
            words = detect_text(contents, lang)
        keyword_tag = OCRTag.objects.create(video=video_obj, words=words[0],
                                            frame_in=int(slot_time * video_obj.frame_rate),
                                            frame_out=int((slot/5) * video_obj.frame_rate), language=lang)
        keyword_tag.save()

    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.eta += (0.25 / video_obj.duration)
    auto_job.save()
    close_clip(myclip)

@app.task
def email_keywords_reportlab(video_id, email_id):
    video = Video.objects.filter(id=video_id).first()
    pdf_file = '/tmp/{}.pdf'.format(video.title.replace(".mp4", ""))
    pagesize = letter
    width, height = pagesize
    doc = SimpleDocTemplate(pdf_file, topMargin=72, bottonMargin=72, leftMargin=36, rightMargin=36,
                            pagesize=pagesize)

    # Our container for flowable objects
    elements = []

    # A large collection of sytlesheets made for us
    stylesheet = getSampleStyleSheet()
    stylesheet.add(ParagraphStyle(name='centered', alignment=TA_CENTER))

    styleN = ParagraphStyle(name='center', parent=stylesheet['BodyText'], alignment=TA_CENTER)

    # Draw things on the pdf, this is were the pdf gets generated

    # Report title
    elements.append(Table(data=[[Paragraph('TRANSCRIPT REPORT', stylesheet['Heading2'])]], colWidths=[width-72]))
    elements.append(Spacer(1, 5 * mm, ))

    # Report info table
    width = (width - 72) / 4
    remarks = ''
    channel = ''

    if Movie.objects.filter(asset_version__video=video):
        m = Movie.objects.filter(asset_version__video=video).first()
        channel = m.channel.channel_name if m.channel else ''

    if Promo.objects.filter(asset_version__video=video):
        m = Promo.objects.filter(asset_version__video=video).first()
        channel = m.channel.channel_name if m.channel else ''

    video_data = DetailVideoSerializer(video)
    vid_minute,vid_seconds = divmod(video_data.data['duration'], 60)
    file_data = []
    file_data.append([Paragraph('Title', style=styleN), Paragraph(str(video_data.data['title']), styleN)])
    file_data.append([Paragraph('Channel',style=styleN), Paragraph(channel, styleN)])
    file_data.append([Paragraph('Duration',style=styleN), Paragraph("{}.{} minutes".format(int(vid_minute), int(vid_seconds)), styleN)])
    style = [('GRID', (0, 0), (-1, -1), 0.75, colors.grey)]
    elements.append(Table(data=file_data, colWidths=[width] + [3*width], style=style, hAlign='LEFT'))
    elements.append(Spacer(1, 10 * mm, ))

    header_data = []
    header_data.append([Paragraph('SNP Edits', stylesheet["Heading2"])])
    elements.append(Table(data=header_data, colWidths=[width - 72]))
    elements.append(Spacer(1, 5 * mm, ))

    # Table inner cells
    data = []
    width = (width - 72) / 18

    frame_tags = video.keywords.all().order_by('frame_in')

    for i, tag in enumerate(frame_tags):
        #tagname = Paragraph(frametag_serializer.data['tagname'], styleN)
        # category = Paragraph(frametag_serializer.data['category'], styleN)
        frame_in = Paragraph(tag._time_in(), styleN)
        frame_out = Paragraph(tag._time_out(), styleN)
        comment = Paragraph(str(tag.words), styleN)
        data.append([frame_in, frame_out, comment])

    style = [('GRID', (0, 0), (-1, -1), 0.75, colors.grey),
             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
             ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
             ('TEXTCOLOR', (0, 0), (-1, 0), colors.black)]
    data = sorted(data, key = lambda x: str(x[0]))
    data = [['Time In', 'Time Out', 'Transcript']] + data
    elements.append(Table(data=data, colWidths=3 * [10 * width] + [20 * width], style=style))
    elements.append(Spacer(1, 10 * mm, ))
    
    # build the doc from elements
    doc.build(elements)
    email = EmailMessage(
        'Transcript Report for {}'.format(video.title),
        'Please Find attached the transcripts \n\n',
        'manan@tessact.com', 
        [email_id]
    )
    email.attach_file(pdf_file)
    email.send()
    silentremove(pdf_file)

    return True

@app.task
def email_keywords_excel(video_id, email_id):
    video = Video.objects.filter(id=video_id).first()
    csv_file = '/tmp/{}.csv'.format(video.title.replace(".mp4", ""))

    frame_tags = video.keywords.all().order_by('frame_in')

    data = []
    for i, tag in enumerate(frame_tags):
        #tagname = Paragraph(frametag_serializer.data['tagname'], styleN)
        # category = Paragraph(frametag_serializer.data['category'], styleN)
        frame_in = tag._time_in()[:7]
        frame_out = tag._time_out()[:7]
        comment = str(tag.words)
        foul_words = []
        for word in aajtak_list:
            if word in comment:
                foul_words.append(word)

        if foul_words:
            data.append([frame_in, frame_out, comment, ", ".join(foul_words)])
        else:
            data.append([frame_in, frame_out, comment, ''])

    data = sorted(data, key = lambda x: str(x[0]))
    transcript_df = pd.DataFrame(data, columns=['Time In', 'Time Out', 'Transcript', "Identified Key Word"])
    transcript_df.to_csv(csv_file, index=False)


    email = EmailMessage(
        'Transcript Report for {}'.format(video.title),
        'Please Find attached the transcripts \n\n',
        'manan@tessact.com', 
        [email_id]
    )
    email.attach_file(csv_file)
    email.send()
    silentremove(csv_file)

    return True

@app.task
def email_count_keywords(channels):

    email = EmailMessage(
    'Transcript Report for {}'.format("republic"),
        'Please Find attached the transcripts \n\n',
            'manan@tessact.com',
                ["manan@tessact.com"]
                )

    for channel in channels:
        channel_videos = [str(x) for x in Promo.objects.filter(channel__channel_name=channel).values_list("asset_version__video__id", flat=True)]
        channel_keyword_tags = KeywordTag.objects.filter(video__id__in=channel_videos)
        word_count  = []
        for each in aajtak_list:
            c = 0
            for tag in channel_keyword_tags:
                if each.strip() in tag.words.strip():
                    c += 1
            word_count.append(c)
        df = pd.DataFrame()
        df['words'] = aajtak_list
        df['word_count'] = word_count
        df.to_excel("{}.xlsx".format(channel), index=False)
        email.attach_file("{}.xlsx".format(channel))
    email.send()

    return True

@app.task
def dump_transcripts_channel(channels):

    email = EmailMessage(
    'Transcript Report for {}'.format("republic"),
        'Please Find attached the transcripts \n\n',
            'manan@tessact.com',
                ["manan@tessact.com"]
                )

    for channel in channels:
        channel_videos = [str(x) for x in Promo.objects.filter(channel__channel_name=channel).values_list("asset_version__video__id", flat=True)]
        channel_keyword_tags = KeywordTag.objects.filter(video__id__in=channel_videos)
        words  = []
        for tag in channel_keyword_tags:
            words.append(tag.words.strip())
        df = pd.DataFrame()
        df['Transcript'] = words
        df.to_excel("{}.xlsx".format(channel), index=False)
        email.attach_file("{}.xlsx".format(channel))
    email.send()

    return True

@app.task
def email_video_transcripts_channels(channels):

    email = EmailMessage(
    'Transcript Report for {}'.format(" ".join(channels)),
        'Please Find attached the transcripts \n\n',
            'manan@tessact.com',
                ["manan@tessact.com"]
                )

    for channel in channels:
        channel_videos = Video.objects.filter(id__in=[str(x) for x in Promo.objects.filter(channel__channel_name=channel)\
            .values_list("asset_version__video__id", flat=True)])

        for channel_video in channel_videos:
            data = []
            keywords = channel_video.keywords.all().order_by("frame_in")
            for tag in keywords:
                frame_in = tag._time_in()[:7]
                frame_out = tag._time_out()[:7]
                comment = str(tag.words)
                data.append([frame_in, frame_out, comment])
            df = pd.DataFrame(data, columns=['Time In', 'Time Out', 'Transcript'])
            df.to_excel("{}_{}.xlsx".format(channel_video.title.strip(".mp4"), channel), index=False)
            email.attach_file("{}_{}.xlsx".format(channel_video.title.strip(".mp4"), channel))

    email.send()
    for channel in channels:
        for channel_video in channel_videos:
            silentremove("{}_{}.xlsx".format(channel_video.title.strip(".mp4"), channel))

    return True


@app.task
def merge_text_detections(t, video_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    keywords = video_obj.ocrtags.all().order_by('frame_in')
    tmp_keyword = None
    for keyword_tag in keywords:
        if not tmp_keyword:
            tmp_keyword = keyword_tag
        else:
            word_1 = keyword_tag.words
            word_2 = tmp_keyword.words
            if difflib.SequenceMatcher(None, word_1, word_2).ratio()>0.8:
                keyword_tag.words = word_2 if len(word_2)>=len(word_1) else word_1
                keyword_tag.frame_in = tmp_keyword.frame_in
                keyword_tag.save()
                tmp_keyword.delete()
                tmp_keyword = keyword_tag
            else:
                tmp_keyword = keyword_tag
    # keywords = video_obj.ocrtags.all().order_by('frame_in')
    # for keyword_tag in keywords:
    #     lang = keyword_tag.language
    #     words = " ".join(keyword_tag.words.split('\n'))
        # if lang != "pa":
        #     text = translate_text(lang, 'pa', words)
        #     keyword_tag = OCRTag.objects.create(video=video_obj, words=text,
        #                                         frame_in=keyword_tag.frame_in, frame_out=keyword_tag.frame_out,
        #                                         language='pa')
        #     keyword_tag.save()
        # if lang != "hi":
        #     text = translate_text(lang, 'hi', words)
        #     keyword_tag = OCRTag.objects.create(video=video_obj, words=text,
        #                                         frame_in=keyword_tag.frame_in, frame_out=keyword_tag.frame_out,
        #                                         language='hi')
        #     keyword_tag.save()
        # if lang != "en":
        #     text = translate_text(lang, 'en', words)
        #     keyword_tag = OCRTag.objects.create(video=video_obj, words=text,
        #                                         frame_in=keyword_tag.frame_in, frame_out=keyword_tag.frame_out,
        #                                         language='en')
        #     keyword_tag.save()
        # if lang != "ta":
        #     text = translate_text(lang, 'ta', words)
        #     keyword_tag = OCRTag.objects.create(video=video_obj, words=text,
        #                                         frame_in=keyword_tag.frame_in, frame_out=keyword_tag.frame_out,
        #                                         language='ta')
        #     keyword_tag.save()


@app.task
def chord_clean_video_file(tmp_file_name, job_id):
    return clean_video_file(tmp_file_name, job_id)


@app.task(on_failure=failure_response)
def background_detect_text(input_file, video_id, job_id=None, time_in=None, time_out=None, lang='en', add_sentiment=False, tmp_file_name=None):
    # tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4()) + '.mp4')
    print(tmp_file_name)
    check_or_create_file(tmp_file_name)
    # urlretrieve(input_file, tmp_file_name)
    with requests.get(input_file, stream=True) as r:
        with open(tmp_file_name, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    video_obj = get_object_or_404(Video, pk=video_id)
    keywords = OCRTag.objects.all().filter(video=video_obj)
    for keyword in keywords:
        keyword.delete()
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    # chord is used because no task should wait for another task to complete
    start_time = 4 if not time_in else int(time_in*2)
    end_time = 4*int(video_obj.duration) if not time_out else int(time_out*2)
    res = chord(
        (detect_text_in_slot.s(st, tmp_file_name, video_id, auto_job.id, lang, add_sentiment) for st in range(1, int(video_obj.duration)*5)),
        chord_clean_video_file.s(tmp_file_name, job_id))
    # merge texts which appear close by
    res_clean = chain(res, merge_text_detections.s(video_id))
    res_clean.apply_async()
    auto_job.job_status = 'PRD'
    auto_job.save()
    index_ocr.delay(video_id)

@app.task
def clean_video_file(file_name, job_id):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    silentremove(file_name)
    # create Keyword and save for the sentences
    auto_job.job_status = 'PRD'
    auto_job.eta = 1.0
    auto_job.save()


@app.task
def list_actors(dummy_arg, video_id):
    video_obj = get_object_or_404(Video, pk=video_id)
    face_groups = FaceGroup.objects.all().filter(video=video_obj)
    persons = []

    for face_group in face_groups:
        try:
            print(face_group.person.name)
            persons.append(face_group.person.name)
        except AttributeError:
            print("None")

    # load the trivia
    trivia = []
    with open('./content/trivia.json', 'r+') as f:
        trivia_obj = json.load(f)
        for person in persons:
            try:
                trivia += trivia_obj[person]
            except KeyError:
                pass
    print(trivia)


@app.task(on_failure=failure_response)
def background_video_processing_trivia(input_file, video_id, job_id, tmp_file_name):
    """Process the video for face matching and generate TriviaSuggestions"""
    print(input_file)
    # tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4()) + '.mp4')
    print(tmp_file_name)
    check_or_create_file(tmp_file_name)
    # urlretrieve(input_file, tmp_file_name)
    with requests.get(input_file, stream=True) as r:
        with open(tmp_file_name, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    video_obj = get_object_or_404(Video, pk=video_id)
    face_groups = FaceGroup.objects.all().filter(video=video_obj)
    # for face_group in face_groups:
    #     face_group.video = None
    #     face_group.save()
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    # chord is used because no task should wait for another task to complete
    res = chord(
        (detect_faces_in_slot.s(st, tmp_file_name, video_id, auto_job.id) for st in range(1, int(video_obj.duration))),
        face_matching.s(video_id, job_id, tmp_file_name))
    fres = list_actors.s(video_id)
    fres.apply_async()


def parse_credits(text, d):
    credits = {}
    last = ""
    for t in text:
        truth = list(map(lambda x: x in d and len(x)>3, t.split(' ')))
        if any(truth):
            credits[t] = []
            last = t
        else:
            if len(last)>0:
                credits[last].append(t)
    return credits


def get_text_for_segment(frame_cut, lang):
    try:
        im = PIL.Image.fromarray(frame_cut)

        with io.BytesIO() as output:
            im.save(output, format="PNG")
            contents = output.getvalue()
            words = detect_text(contents, lang)
        split_text = words[0].lower().split('\n')
    except AttributeError:
        split_text = []
        pass
    return split_text


@app.task
def background_rolling_credit(input_file, video_id, job_id, time_in=None, time_out=None):
    """Process the video for rolling credits"""
    # print(input_file)
    # tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4()) + '.mp4')
    # print(tmp_file_name)
    # check_or_create_file(tmp_file_name)
    # urlretrieve(input_file, tmp_file_name)
    # with requests.get(input_file, stream=True) as r:
    #     with open(tmp_file_name, 'wb') as f:
    #         shutil.copyfileobj(r.raw, f)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    video_obj = get_object_or_404(Video, pk=video_id)

    # clear old credits
    try:
        old_credit_obj = Credit.objects.filter(video=video_obj)
        for e_credit_obj in old_credit_obj:
            e_credit_obj.delete()
    except ObjectDoesNotExist:
        pass

    # initiate request
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()

    # params for ShiTomasi corner detection
    # feature_params = dict(maxCorners=100,
    #                       qualityLevel=0.3,
    #                       minDistance=7,
    #                       blockSize=7)
    # # Parameters for lucas kanade optical flow
    # lk_params = dict(winSize=(15, 15),
    #                  maxLevel=2,
    #                  criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
    # # Create some random colors
    # color = np.random.randint(0, 255, (100, 3))
    #
    # myclip = VideoFileClip(tmp_file_name)
    # print("time in: {}, out: {}".format(str(time_in), str(time_out)))
    # if time_in is not None and time_out is not None:
    #     myclip = myclip.subclip(time_in, time_out)
    # clip = False
    # first_frame = None
    # second_frame = None
    # just_one = True
    # median_velocity = []
    # first_frame_static = None
    # frame_cut = None
    # full_frame_cut = None
    # split_text = []
    # for im in tqdm.tqdm(myclip.iter_frames()):
    #     if first_frame is None:
    #         first_frame = im
    #         first_frame_static = im
    #         first_gray = cv2.cvtColor(first_frame, cv2.COLOR_RGB2GRAY)
    #         mask = np.zeros_like(first_gray)
    #         p0 = cv2.goodFeaturesToTrack(first_gray, mask=None, **feature_params)
    #     else:
    #         mask = np.zeros_like(first_gray)
    #         p0 = cv2.goodFeaturesToTrack(first_gray, mask=None, **feature_params)
    #         second_frame = im
    #         second_grey = cv2.cvtColor(second_frame, cv2.COLOR_RGB2GRAY)
    #         try:
    #             p1, st, err = cv2.calcOpticalFlowPyrLK(first_gray, second_grey, p0, None, **lk_params)
    #         except cv2.error:
    #             first_gray = second_grey.copy()
    #             continue
    #         good_new = p1[st == 1]
    #         good_old = p0[st == 1]
    #         velocity = []
    #         for i, (new, old) in enumerate(zip(good_new, good_old)):
    #             a, b = new.ravel()
    #             c, d = old.ravel()
    #             if b > im.shape[0] / 2 - 100 and d < im.shape[0] / 2 + 100 and d - b > 1:
    #                 velocity.append(int(d - b))
    #             mask = cv2.line(mask, (a, b), (c, d), color[i].tolist(), 2)
    #         median_velocity.append(np.median(velocity))
    #         # Now update the previous frame
    #         first_gray = second_grey.copy()
    #         try:
    #             if frame_cut is None:
    #                 frame_cut = second_grey[int(im.shape[0]/2):int(im.shape[0]/2+np.median(velocity)), 0:im.shape[1]]
    #             else:
    #                 new_frame_cut = second_grey[int(im.shape[0]/2):int(im.shape[0]/2+np.median(velocity)), 0:im.shape[1]]
    #                 frame_cut = np.concatenate((frame_cut, new_frame_cut))
    #                 if frame_cut.shape[0]>3000:
    #                     split_text_for_segment = get_text_for_segment(frame_cut, "en")
    #                     if split_text:
    #                         split_text+=split_text_for_segment
    #                     else:
    #                         split_text = split_text_for_segment
    #
    #                     if full_frame_cut is None:
    #                         full_frame_cut = frame_cut
    #                     else:
    #                         full_frame_cut = np.concatenate((full_frame_cut, frame_cut))
    #                     frame_cut = None
    #         except ValueError:
    #             pass
    # if full_frame_cut is None:
    #     full_frame_cut = frame_cut
    #     split_text = get_text_for_segment(frame_cut, "en")
    # cv2.destroyAllWindows()
    #
    # # print(split_text)
    # with open('utils/titles.txt', 'r+') as f:
    #     titles = " ".join(f.read().split('\n')).split(' ')
    #     # print(titles)
    # credit_obj = parse_credits(split_text, titles)
    # logger.debug(credit_obj)
    #
    # credit_db_obj = Credit.objects.create(video=video_obj, credit=credit_obj)
    # credit_db_obj.save()
    #
    # close_clip(myclip)
    #
    # clean_video_file(tmp_file_name, job_id)


@app.task(on_failure=failure_response)
def backgroundprocess_sentiment(input_file, video_id, job_id=None, language="en-IN", tmp_file_name=None):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    # delete all the old keyword tags
    video_obj = get_object_or_404(Video, pk=video_id)
    keywords = KeywordTag.objects.all().filter(video=video_obj)
    for keyword in keywords:
        keyword.delete()
    # get the video and audio
    print(input_file)
    tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4()) + '.mp4')
    print(tmp_file_name)
    check_or_create_file(tmp_file_name)
    # urlretrieve(input_file, tmp_file_name)
    with requests.get(input_file, stream=True) as r:
        with open(tmp_file_name, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    output_audio_file = os.path.join("/tmp/audio/", str(uuid.uuid4()) + '.mp3')
    check_or_create_file(output_audio_file)
    command = [FFMPEG_BIN,
               # '-v', 'quiet',
               '-i', tmp_file_name,
               # '-codec:a', 'libmp3lame',
               # '-qscale:a', '2',
               output_audio_file]
    output = sp.check_output(command)
    auto_job = AutoVideoJob.objects.get(id=job_id)
    # process audio for sentences
    break_audio(output_audio_file, '/tmp/audio/', language, 30, video_id, job_id)

    # create Keyword and save for the sentences
    auto_job.job_status = 'PRD'
    auto_job.eta = 1.0
    auto_job.save()
    silentremove(tmp_file_name)
    silentremove(output_audio_file)


@app.task(on_failure=failure_response, max_retries=1)
def backgroundprocess_emotion(input_file, video_id, job_id=None, tmp_file_name=None):
    auto_job = AutoVideoJob.objects.get(id=job_id)
    auto_job.job_status = 'PRO'
    auto_job.eta = 0
    auto_job.save()
    video_obj = get_object_or_404(Video, pk=video_id)

    # tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4()) + '.mp4')

    check_or_create_file(tmp_file_name)
    # urlretrieve(input_file, tmp_file_name)
    with requests.get(input_file, stream=True) as r:
        with open(tmp_file_name, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    output_audio_file = os.path.join("/tmp/audio/", str(uuid.uuid4()) + '.wav')
    check_or_create_file(output_audio_file)
    command = [FFMPEG_BIN,
               # '-v', 'quiet',
               '-i', tmp_file_name,
               '-ac', '1',
               '-ar', '16000',
               output_audio_file]
    output = sp.check_output(command)

    y, sr = librosa.load(output_audio_file)

    BINS_PER_OCTAVE = 12 * 3
    N_OCTAVES = 7
    C = librosa.amplitude_to_db(librosa.cqt(y=y, sr=sr,
                                            bins_per_octave=BINS_PER_OCTAVE,
                                            n_bins=N_OCTAVES * BINS_PER_OCTAVE),
                                ref=np.max)

    ##########################################################
    # To reduce dimensionality, we'll beat-synchronous the CQT
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, trim=False)
    Csync = librosa.util.sync(C, beats, aggregate=np.median)

    beat_times = librosa.frames_to_time(librosa.util.fix_frames(beats,
                                                                x_min=0,
                                                                x_max=C.shape[1]),
                                        sr=sr)

    R = librosa.segment.recurrence_matrix(Csync, width=3, mode='affinity',
                                          sym=True)

    # Enhance diagonals with a median filter (Equation 2)
    df = librosa.segment.timelag_filter(scipy.ndimage.median_filter)
    Rf = df(R, size=(1, 7))

    ###################################################################

    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    Msync = librosa.util.sync(mfcc, beats)

    path_distance = np.sum(np.diff(Msync, axis=1) ** 2, axis=0)
    sigma = np.median(path_distance)
    path_sim = np.exp(-path_distance / sigma)

    R_path = np.diag(path_sim, k=1) + np.diag(path_sim, k=-1)

    deg_path = np.sum(R_path, axis=1)
    deg_rec = np.sum(Rf, axis=1)

    mu = deg_path.dot(deg_path + deg_rec) / np.sum((deg_path + deg_rec) ** 2)

    A = mu * Rf + (1 - mu) * R_path

    L = scipy.sparse.csgraph.laplacian(A, normed=True)

    # and its spectral decomposition
    evals, evecs = scipy.linalg.eigh(L)

    # We can clean this up further with a median filter.
    # This can help smooth over small discontinuities
    evecs = scipy.ndimage.median_filter(evecs, size=(9, 1))

    # cumulative normalization is needed for symmetric normalize laplacian eigenvectors
    Cnorm = np.cumsum(evecs ** 2, axis=1) ** 0.5

    k = 5

    X = evecs[:, :k] / Cnorm[:, k - 1:k]

    KM = sklearn.cluster.KMeans(n_clusters=k)

    seg_ids = KM.fit_predict(X)

    # # and plot the results

    #
    d = np.atleast_2d(seg_ids).T

    # Locate segment boundaries from the label sequence
    bound_beats = 1 + np.flatnonzero(seg_ids[:-1] != seg_ids[1:])

    # Count beat 0 as a boundary
    bound_beats = librosa.util.fix_frames(bound_beats, x_min=0)

    # Compute the segment label for each boundary
    bound_segs = list(seg_ids[bound_beats])

    # Convert beat indices to frames
    bound_frames = beats[bound_beats]

    # Make sure we cover to the end of the track
    bound_frames = librosa.util.fix_frames(bound_frames,
                                           x_min=None,
                                           x_max=C.shape[1] - 1)

    bound_times = librosa.frames_to_time(bound_frames)
    freqs = librosa.cqt_frequencies(n_bins=C.shape[0],
                                    fmin=librosa.note_to_hz('C1'),
                                    bins_per_octave=BINS_PER_OCTAVE)

    # librosa.display.specshow(C, y_axis='cqt_hz', sr=sr,
    #                          bins_per_octave=BINS_PER_OCTAVE,
    #                          x_axis='time')

    for interval, label in zip(zip(bound_times, bound_times[1:]), bound_segs):
        e = EmotionTag.objects.create(frame_in=interval[0]*video_obj.frame_rate,
                                      frame_out=interval[1]*video_obj.frame_rate,
                                      emotion_quo=str(label),
                                      video=video_obj
                                      )
        e.save()

    auto_job.eta = 1.0
    auto_job.job_status = "PRD"
    auto_job.save()
    silentremove(tmp_file_name)
    silentremove(output_audio_file)


def load_file(file):
    fingerprints = []
    freq_map = {}
    freq_hash = {}
    with open(file, 'r+') as fp:
        lines = fp.readlines()
        for line in lines:
            mt = [int(m.strip()) for m in line.strip().split(",")]
            if mt[0] > mt[1]:
                ta = [int(mt[0]/2),int(mt[1]/2)]
            else:
                ta = [int(mt[1]/2), int(mt[0]/2)]
            if mt[2] in freq_map.keys():
                if ta[0] not in freq_map[mt[2]]:
                    freq_map[mt[2]].append(ta[0])
                if ta[1] not in freq_map[mt[2]]:
                    freq_map[mt[2]].append(ta[1])
                # freq_hash[ta] =
            else:
                freq_map[mt[2]] = ta
        fingerprints.append(mt)
    return fingerprints, freq_map


def generate_matches(ad, main):
    print(max(ad.keys()), max(main.keys()))
    hits = []
    hit_map = [0]*(max(main.keys())+1)
    for i in tqdm.tqdm(main):
        start = 0
        fails = 0
        for j in sorted(ad.keys()):
            if i+j in main:
                ad_freq_map = ad[j]
                freq_map = main[i+j]
                if sum([t in freq_map for t in ad_freq_map]) > 1:
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

            if fails>10:
                hit_map[i] = 0
                break
    print(len(hits))
    return hit_map


def sec2tcr(secs):
    h = math.floor(secs/3600)
    m = math.floor(secs/60) - h*60
    s = secs%60
    return "{0:02d}:{1:02d}:{2:02d}".format(h,m,s)


# @app.task
# def find_others(tag_id):
#     ptag = PlayoutTag.objects.get(id=tag_id)
#     start = ptag.frame_in/25
#     end = ptag.frame_out/25
#     c_freq_map = {}
#     if start and end:
#         for i in main_freq_map:
#             if start * 24 <= i <= end * 24:
#                 c_freq_map[i - start * 24] = main_freq_map[i]
#     hit_map = generate_matches(c_freq_map, main_freq_map)
#     m = max(c_freq_map.keys())
#     hits = []
#     for v in range(len(hit_map)):
#         if hit_map[v] > int(0.50*m) and abs(int(v/24)-start) > 10:
#             print(sec2tcr(int(v/24)), hit_map[v]/m)
#             if int(v/24) not in hits:
#                 hits.append(int(v/24))
#                 p_tag, c = PlayoutTag.objects.get_or_create(video=ptag.video, frame_in=math.ceil(v/24)*25,
#                                                             frame_out=(math.ceil(v/24)+math.ceil(hit_map[v]/24))*25,
#                                                             content_type=ptag.content_type, object_id=ptag.object_id,
#                                                             object_content_type=ptag.object_content_type,
#                                                             is_original=False)


@app.task
def send_moderation_report(id, groups, emails, username):
    video = Video.objects.get(id=id)

    # users
    recipients = []
    for g in groups.split(","):
        users = User.objects.filter(Q(groups__name=g)).distinct()
        recipients += list(i for i in users.values_list('email', flat=True) if bool(i))
    recipients += emails.split(',')
    recipients_set = set(recipients)
    recipients_list = list(recipients_set)
    print(recipients_list)

    pdf_file = '/tmp/{}.pdf'.format(video.title.replace(".mp4", ""))
    report = SonyReport('pdf_file', 'Letter')
    pdf = report.print_report(video.id, username)

    email = EmailMessage(
        'Compliance Report for {}'.format(video.title),
        'Please Find attached the compliance report file\n\n',
        'aswin@tessact.com',
        recipients_list
    )
    email.attach_file(pdf_file)
    email.send()
    time.sleep(15)

def bulk_update_fingerprints():
    unique_songs = Song.objects.all()
    s3.download_file('audio-fingerprint-data', 'fingerprint.dump', "fingerprint.dump")
    fingerprint_database = joblib.load("fingerprint.dump")
    max_playout = []
    hindi_lis = [1010040, 1010234, 1010700, 1010357, 1010011, 1010465, 1010008, 1010500]
    tamil_lis = [1010182, 1010410, 1010777]
    keys = set(list(fingerprint_database['hindi'].keys()) + list(fingerprint_database['tamil'].keys()))
    if not os.path.exists("/tmp/process"):
        os.mkdir("/tmp/process")
    tot = unique_songs.count()
    print("Total Songs : {}".format(unique_songs.count()))
    c = 0
    for song in unique_songs:
        print("Songs Done : {}/{}".format(c,tot))
        c += 1
        sid = str(song.id)
        if sid not in keys:
            ptags = PlayoutTag.objects.filter(object_id=sid)
            if ptags:
                max_dur = 0
                for tag in ptags:
                    dur = duration = tag.frame_out//25 - tag.frame_in//25
                    if dur > max_dur:
                        max_dur = dur
                        max_tag = tag
                file_link = max_tag.video.file
                video_id = max_tag.video.id
                s3.download_file('barc-music-data', file_link.split(".com/")[-1] , "/tmp/process/{}.mp4".format(str(video_id)))
                channel_id = int(file_link.split(".com/")[-1].split('_')[-1].split('.')[0])
                if channel_id in hindi_lis:
                    language = 'hindi'
                if channel_id in tamil_lis:
                    language = 'tamil'
                print("Fingerprinting Song : {} : Duration: {}".format(sid, max_dur))
                os.system("ffmpeg -v quiet -ss {} -i /tmp/process/{}.mp4 -t {} /tmp/process/{}.mp3 -y".format(tag.frame_in//25, str(video_id), max_dur , sid))
                fingerprint, _ = chromaprint.decode_fingerprint(acoustid.fingerprint_file('/tmp/process/{}.mp3'.format(sid))[1])
                fingerprint_database[language][sid] = fingerprint
                silentremove("/tmp/process/{}.mp3".format(sid))
                silentremove("/tmp/process/{}.mp4".format(str(video_id)))
    joblib.dump(fingerprint_database, "fingerprint.dump")
    s3.upload_file('fingerprint.dump', 'audio-fingerprint-data', 'fingerprint.dump')
    silentremove("fingerprint.dump")

@app.task
def update_fingerprints(start_date=date.today()):
    unique_videos = PlayoutTag.objects.filter(object_id__isnull=False, created_on__date=start_date).values_list("video__id", flat=True).distinct()
    s3.download_file('audio-fingerprint-data', 'fingerprint.dump', "fingerprint.dump")
    fingerprint_database = joblib.load("fingerprint.dump")
    check_dic = {}
    hindi_lis = [1010040, 1010234, 1010700, 1010357, 1010011, 1010465, 1010008, 1010500]
    tamil_lis = [1010182, 1010410, 1010777]
    set_check = set(check_dic.keys())
    for video_id in unique_videos:
        file_link = Video.objects.filter(id=video_id).first().file
        ptags = PlayoutTag.objects.filter(object_id__isnull=False, video__id=video_id)
        if not os.path.exists("/tmp/process"):
            os.mkdir("/tmp/process")
        s3.download_file('barc-music-data', file_link.split(".com/")[-1] , "/tmp/process/{}.mp4".format(str(video_id)))
        channel_id = int(file_link.split(".com/")[-1].split('_')[-1].split('.')[0])
        if channel_id in hindi_lis:
            language = 'hindi'
        if channel_id in tamil_lis:
            language = 'tamil'
        set_db = set(fingerprint_database[language].keys())
        for tag in ptags:
            sid = str(tag.tagged_object.id)
            if sid not in set_db:
                os.system("ffmpeg -v quiet -ss {} -i /tmp/process/{}.mp4 -t {} /tmp/process/{}.mp3 -y".format(tag.frame_in//25, str(video_id), tag.frame_out//25 - tag.frame_in//25 , sid))
                fingerprint, _ = chromaprint.decode_fingerprint(acoustid.fingerprint_file('/tmp/process/{}.mp3'.format(sid))[1])
                #s3.upload_file("/tmp/process/{}.mp3".format(sid), 'audio-fingerprint-data', "{}_{}.mp3".format(sid, duration))
                duration = tag.frame_out//25 - tag.frame_in//25
                print("Fingerprinting Song : {} : Duration: {}".format(sid, duration))
                if sid in set_check:
                        if duration > check_dic[sid]:
                            print("Updating song: {}".format(sid))
                            fingerprint_database[language][sid] = fingerprint
                            check_dic[sid] = duration
                else:
                    fingerprint_database[language][sid] = fingerprint
                    check_dic[sid] = duration
                silentremove("/tmp/process/{}.mp3".format(sid))
        silentremove("/tmp/process/{}.mp4".format(str(video_id)))
    joblib.dump(fingerprint_database, "fingerprint.dump")
    s3.upload_file('fingerprint.dump', 'audio-fingerprint-data', 'fingerprint.dump')
    silentremove("fingerprint.dump")

def fetch_playout(check=False):
    unique_videos = PlayoutTag.objects.filter(object_id=None, is_checked=check).values_list("video__id", flat=True).distinct()
    for vid in unique_videos:
        get_song.delay(vid, check)

@app.task
def get_song(video_id, check):
    file_link = Video.objects.filter(id=video_id).first().file
    ptags = PlayoutTag.objects.filter(object_id=None, video__id=video_id, is_checked=check)
    hindi_lis = [1010040, 1010234, 1010700, 1010357, 1010011, 1010465, 1010008, 1010500]
    tamil_lis = [1010182, 1010410, 1010777]
    s3.download_file('audio-fingerprint-data', 'fingerprint.dump', "fingerprint.dump")
    if not os.path.exists("/tmp/process"):
        os.mkdir("/tmp/process")
    fingerprint_database = joblib.load("fingerprint.dump")
    s3.download_file('barc-music-data', file_link.split(".com/")[-1] , "/tmp/process/{}.mp4".format(str(video_id)))
    for tag in ptags:
        start_time = time.time()
        os.system("ffmpeg -v quiet -ss {} -i /tmp/process/{}.mp4 -t {} /tmp/process/{}.mp3 -y".format(tag.frame_in//25, str(video_id), tag.frame_out//25 - tag.frame_in//25 , str(tag.id)))
        try:
            source_fingerprint, _ = chromaprint.decode_fingerprint(acoustid.fingerprint_file('/tmp/process/{}.mp3'.format(str(tag.id)))[1])
        except Exception as e:
            print(e)
            print(tag.frame_in//25, tag.frame_out//25, str(tag.id))
            continue
        source_fingerprint = [x//1000000 for x in source_fingerprint]
        rank = 0
        song_uuid = ''
        channel_id = int(file_link.split(".com/")[-1].split('_')[-1].split('.')[0])
        if channel_id in hindi_lis:
            language = 'hindi'
        if channel_id in tamil_lis:
            language = 'tamil'
        for key in fingerprint_database[language].keys():
            c = 0
            tmp_set = set(fingerprint_database[language][key])
            for each in source_fingerprint:
                if each in tmp_set:
                    c += 1
            if c > rank:
                rank = c
                song_uuid = key
        if rank/948 > 0.5:
            tag.object_id = song_uuid
            tag.object_content_type = ContentType.objects.get(id=57)
            tag.is_checked = True
            tag.save()
        else:
            tag.is_checked = True
            tag.save()
        silentremove("/tmp/process/{}.mp3".format(str(tag.id)))
    silentremove("/tmp/process/{}.mp4".format(str(video_id)))

# @periodic_task(run_every=crontab(minute=0, hour='1'))
# def update_fingerrpints_tag():
#     bulk_update_fingerprints()
#     fetch_playout()
# last_created_on =

@app.task(name='update_batch')
def check_and_update_batch(arg):

    def filter_batch_videos(new_batch_videos):
        for i in new_batch_videos:
            asset_ver_content_type = AssetVersion.objects.filter(video=i).last()
            if (asset_ver_content_type and asset_ver_content_type.content_type.app_label == "content" \
                and asset_ver_content_type.content_type.model == "promo"):
                new_batch_videos = new_batch_videos.exclude(id=i.id)
            if("/Master/" in i.file or "/Intermediate/" in i.file):
                new_batch_videos = new_batch_videos.exclude(id=i.id)

        return new_batch_videos


    time_in = None
    time_out = None
    curr_time = timezone.now()

    if Batch.objects.count() == 0: #when there is no batch
        batch = Batch.objects.create(last_created_on=curr_time)
        VideoProcessingStatus.objects.create(batch=batch, processed=True, completed=True)

    batch = Batch.objects.order_by('last_created_on').last()
    batchvideos_status = VideoProcessingStatus.objects.filter(batch=batch).values_list('processed',flat=True)

    if batchvideos_status:
        batch_status = reduce(and_, batchvideos_status)
    else:
        batch_status = False

    if(batch_status):
        batch.processed=True
        batch.save()

        new_batch_videos = Video.objects.filter(created_on__gt=batch.last_created_on,
                                                 created_on__lte=curr_time)

        new_batch_videos = filter_batch_videos(new_batch_videos)
        # for i in new_batch_videos:
        #     asset_ver_content_type = AssetVersion.objects.filter(video=i).last()
        #     if (asset_ver_content_type and asset_ver_content_type.content_type.app_label == "content" \
        #         and asset_ver_content_type.content_type.model == "promo"):
        #         new_batch_videos = new_batch_videos.exclude(id=i.id)
        #     if "/Master/" or "/Intermediate/" in i.file:
        #         new_batch_videos = new_batch_videos.exclude(id=i.id)
        #assetversion.objects.filter(video=video_id)
        #if promos is the content type the remove the fcuk out of the new_batch video else lettttttiB!!


        if(new_batch_videos.count() > 0):
            new_batch = Batch.objects.create(last_created_on=curr_time)

            if new_batch:
                logging.debug("New batch created with last_created_on as", batch.last_created_on)

                for instance in new_batch_videos:
                    video_processing_status_instance, _ = VideoProcessingStatus.objects.get_or_create(batch=new_batch, video=instance)

#                    job_type_instance_identify_faces, _ = JobType.objects.get_or_create(name='Identify Faces')
#                    job_type_instance_hardcuts, _ = JobType.objects.get_or_create(name='Generate Hardcuts')
#                    job_type_instance_match_faces, _ = JobType.objects.get_or_create(name='Match Faces')
#                    job_type_instance_find_keywords, _ = JobType.objects.get_or_create(name='Find Keywords')
#                    job_type_instance_detect_text, _ = JobType.objects.get_or_create(name='Detect Text')
#                    job_type_instance_detect_objects, _ = JobType.objects.get_or_create(name='Identify Objects')
#                    job_type_instance_detect_emotions, _ = JobType.objects.get_or_create(name='Identify Emotion')
                    # u = User.objects.get(username='test_user')

#                    auto_generate_hardcuts = AutoVideoJob.objects.create(created_by=None, video=instance,
#                                            job_type=job_type_instance_hardcuts, eta=0)
#                    auto_identify_faces = AutoVideoJob.objects.create(created_by=None, video=instance,
#                                            job_type=job_type_instance_identify_faces, eta=0)
#                    auto_match_faces = AutoVideoJob.objects.create(created_by=None, video=instance,
#                                            job_type=job_type_instance_match_faces, eta=0)
#                    auto_generate_keywords = AutoVideoJob.objects.create(created_by=None, video=instance,
#                                            job_type=job_type_instance_find_keywords, eta=0)
#                    auto_generate_ocr = AutoVideoJob.objects.create(created_by=None, video=instance,
#                                            job_type=job_type_instance_detect_text, eta=0)
#                    auto_generate_objects = AutoVideoJob.objects.create(created_by=None, video=instance,
#                                            job_type=job_type_instance_detect_objects, eta=0)
#                    auto_generate_emotions = AutoVideoJob.objects.create(created_by=None, video=instance,
#                                            job_type=job_type_instance_detect_emotions, eta=0)

    return "Batch Success"

#TASK TO BE REPEATED AFTER EVERY 5 MINUTES.
@app.task(name='update_process_status')
def update_process_status(arg):

    #Check for videos in that particular batch only.
    batch = Batch.objects.order_by('last_created_on').last()
    video_processing_status_instances =  VideoProcessingStatus.objects.filter(batch=batch)

    for i in video_processing_status_instances:
        video_id = str(i.video.id)
        auto_jobs = AutoVideoJob.objects.filter(video=video_id)
        print("inside for loop", auto_jobs)

        req_param = ["PRD", "FAI"]

        # For storing job_status , processed & completed for each job of the video dynamically.
        processes = dict()

        for job in auto_jobs:
            processed = False
            completed = False

            #Check if the job has failed or executed sucessfully.
            if(str(job.job_status) in req_param):
                processed = True

            if(str(job.job_status) == "PRD"):
                completed = True
            processes.update({str(job.job_type).replace(" ", "_") : {"job_status" : str(job.job_status), "processed": processed, "completed": completed}})

        #Check if all the jobs of the video have been processed and completed.
        processed = ""
        completed = ""
        for process in processes.values():
            if processed == "":
                processed = process["processed"]
            else:
                processed = process["processed"] and processed

            if completed == "":
                completed = process["completed"]
            else:
                completed = process["completed"] and completed

        i.processed = processed
        i.completed = completed
        i.save()

    logging.debug("Success")
    return "Success"

def get_document(id):
    try:
        doc = es.get(id=id, index='asearch')
        return doc["_source"]
    except NotFoundError as e:
        return None

def update_document(id, doc):
    es.update(index='asearch', doc_type='docs', id=id, body={"doc" :doc})

@app.task
def index_faces_azure(video_id):
    video = Video.objects.filter(id=video_id).first()
    index_list = []
    if video:
        framerate = int(video.frame_rate)
        video_id = str(video.id)
        video_cuts = ManualTag.objects.filter(video=video_id).order_by('frame_in')
        asset = AssetVersion.objects.filter(video=video_id).first()
        asset_id = asset.id
        video_title = video.title
        content_type = asset.content_type.id
        for cuts in video_cuts:
            cuts_id = str(cuts.id)
            doc = get_document(cuts_id)
            if doc:
                doc['contact'] = []
                person_tags = video.facegroup_set.all()
                for person_tag in person_tags:
                    if person_tag.person:
                        timeline = sorted(person_tag.timeline)
                        for times in timeline:
                            if times >= cuts.frame_in / framerate and times <= cuts.frame_out / framerate:
                                doc['contact'].append(person_tag.person.name.upper())
                                break
                update_document(cuts_id, doc)

            else:
                index_dict = {"_id": str(cuts.id) ,"_index": "asearch", "_type": "docs", "_source": {'time_in':cuts.frame_in / framerate, 'time_out': cuts.frame_out / framerate, "asset": asset_id, \
                                'id': str(cuts.id), 'object': [], 'ocr': "", 'stt': "", "contact": [], "emotion": [], "shots": [], "location": [] ,"title": video_title, "content_type":content_type}}
                person_tags = video.facegroup_set.all()
                for person_tag in person_tags:
                    if person_tag.person:
                        timeline = sorted(person_tag.timeline)
                        for times in timeline:
                            if times >= cuts.frame_in / framerate and times <= cuts.frame_out / framerate:
                                index_dict['_source']['contact'].append(person_tag.person.name.upper())
                                break
                index_list.append(index_dict)
    if index_list:
        helpers.bulk(es, index_list)



@app.task
def index_emotions_azure(video_id):
    video = Video.objects.filter(id=video_id).first()
    index_list = []
    if video:
        framerate = int(video.frame_rate)
        video_id = str(video.id)
        video_cuts = ManualTag.objects.filter(video=video_id).order_by('frame_in')
        asset = AssetVersion.objects.filter(video=video_id).first()
        asset_id = asset.id
        video_title = video.title
        content_type = asset.content_type.id
        for cuts in video_cuts:
            cuts_id = str(cuts.id)
            doc = get_document(cuts_id)
            if doc:
                doc['emotion'] = []
                emotions = [x['emotion'] for x in Face.objects.filter(face_group__video=video, face_rect__frame__videoframe__time__gte=cuts._seconds_in(), face_rect__frame__videoframe__time__lte=cuts._seconds_out()).values("emotion").distinct() if x['emotion'] != 'neutral']
                emotion_list = [x.replace("happiness", "happy").replace("sadness", 'sad').upper() for x in emotions]
                if emotion_list:
                    doc['emotion'].extend(emotion_list)
                update_document(cuts_id, doc)
            else:
                index_dict = {"_id": str(cuts.id) ,"_index": "asearch", "_type": "docs", "_source": {'time_in':cuts.frame_in / framerate, 'time_out': cuts.frame_out / framerate, "asset": asset_id, \
                                'id': str(cuts.id), 'object': [], 'ocr': "", 'stt': "", "contact": [], "emotion": [], "shots": [], "location": [], "title": video_title, "content_type":content_type}}
                emotions = [x['emotion'] for x in Face.objects.filter(face_group__video=video, face_rect__frame__videoframe__time__gte=cuts._seconds_in(), face_rect__frame__videoframe__time__lte=cuts._seconds_out()).values("emotion").distinct() if x['emotion'] != 'neutral']
                emotion_list = [x.replace("happiness", "happy").replace("sadness", 'sad').upper() for x in emotions]
                if emotion_list:
                    index_dict['_source']['emotion'].extend(emotion_list)
                index_list.append(index_dict)
    if index_list:
        helpers.bulk(es, index_list)

@app.task
def index_emotions_aws(video_id):
    video = Video.objects.filter(id=video_id).first()
    index_list = []
    if video:
        framerate = int(video.frame_rate)
        video_id = str(video.id)
        video_cuts = ManualTag.objects.filter(video=video_id).order_by('frame_in')
        asset = AssetVersion.objects.filter(video=video_id).first()
        asset_id = asset.id
        video_title = video.title
        content_type = asset.content_type.id
        for cuts in video_cuts:
            cuts_id = str(cuts.id)
            doc = get_document(cuts_id)
            if doc:
                doc['emotion'] = []
                emotion_list = [x['emotion_quo'].upper().strip() for x in EmotionTag.objects.filter(video__id=video_id).filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("emotion_quo").distinct() if x['emotion_quo']]
                if emotion_list:
                    doc['emotion'].extend(emotion_list)
                update_document(cuts_id, doc)
            else:
                index_dict = {"_id": str(cuts.id) ,"_index": "asearch", "_type": "docs", "_source": {'time_in':cuts.frame_in / framerate, 'time_out': cuts.frame_out / framerate, "asset": asset_id, \
                                'id': str(cuts.id), 'object': [], 'ocr': "", 'stt': "", "contact": [], "emotion": [], "shots": [], "location": [], "title": video_title, "content_type":content_type}}
                emotion_list = [x['emotion_quo'].upper().strip() for x in EmotionTag.objects.filter(video__id=video_id).filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("emotion_quo").distinct() if x['emotion_quo']]
                if emotion_list:
                    index_dict['_source']['emotion'].extend(emotion_list)
                index_list.append(index_dict)
    if index_list:
        helpers.bulk(es, index_list)


@app.task
def index_locations(video_id):
    video = Video.objects.filter(id=video_id).first()
    index_list = []
    if video:
        framerate = int(video.frame_rate)
        video_id = str(video.id)
        video_cuts = ManualTag.objects.filter(video=video_id).order_by('frame_in')
        asset = AssetVersion.objects.filter(video=video_id).first()
        asset_id = asset.id
        video_title = video.title
        content_type = asset.content_type.id
        for cuts in video_cuts:
            cuts_id = str(cuts.id)
            doc = get_document(cuts_id)
            if doc:
                update_document(cuts_id, doc)
            else:
                index_dict = {"_id": str(cuts.id) ,"_index": "asearch", "_type": "docs", "_source": {'time_in':cuts.frame_in / framerate, 'time_out': cuts.frame_out / framerate, "asset": asset_id, \
                                'id': str(cuts.id), 'object': [], 'ocr': "", 'stt': "", "contact": [], "emotion": [], "shots": [], "location": [], "title": video_title, "content_type":content_type}}
                cut_tags = cuts.tags.filter(tags__parent__title__iexact="Location")
                if cut_tags:
                    for tag in cut_tags:
                        index_dict['_source']['location'].append("{} {}".format(tag.title.upper()))
                index_list.append(index_dict)
    if index_list:
        helpers.bulk(es, index_list)


def index_locations_tessact(video_id):
    video = Video.objects.filter(id=video_id).first()
    index_list = []
    if video:
        framerate = int(video.frame_rate)
        video_id = str(video.id)
        video_cuts = ManualTag.objects.filter(video=video_id).order_by('frame_in')
        asset = AssetVersion.objects.filter(video=video_id).first()
        asset_id = asset.id
        video_title = video.title
        content_type = asset.content_type.id
        for cuts in video_cuts:
            cuts_id = str(cuts.id)
            doc = get_document(cuts_id)
            if doc:
                update_document(cuts_id, doc)
            else:
                index_dict = {"_id": str(cuts.id) ,"_index": "asearch", "_type": "docs", "_source": {'time_in':cuts.frame_in / framerate, 'time_out': cuts.frame_out / framerate, "asset": asset_id, \
                                'id': str(cuts.id), 'object': [], 'ocr': "", 'stt': "", "contact": [], "emotion": [], "shots": [], "location": [], "title": video_title, "content_type":content_type}}
                cut_objects = [x['words'].upper().strip() for x in FrameTag.objects.filter(video__id=video_id, tag__parent__title__iexact="Location").filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("words").distinct() if x['words']]
                if cut_objects:
                    index_dict['_source']['location'].extend(cut_objects)
                index_list.append(index_dict)
    if index_list:
        helpers.bulk(es, index_list)


def index_objects(video_id):
    video = Video.objects.filter(id=video_id).first()
    index_list = []
    if video:
        framerate = int(video.frame_rate)
        video_id = str(video.id)
        video_cuts = ManualTag.objects.filter(video=video_id).order_by('frame_in')
        asset = AssetVersion.objects.filter(video=video_id).first()
        asset_id = asset.id
        video_title = video.title
        content_type = asset.content_type.id
        for cuts in video_cuts:
            cuts_id = str(cuts.id)
            doc = get_document(cuts_id)
            if doc:
                doc['object'] = []
                cut_objects = [x['words'].upper().strip() for x in FrameTag.objects.filter(video__id=video_id, tag__parent__title__iexact="Others").filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("words").distinct() if x['words']]
                if cut_objects:
                    doc['object'].extend(cut_objects)
                update_document(cuts_id, doc)
            else:
                index_dict = {"_id": str(cuts.id) ,"_index": "asearch", "_type": "docs", "_source": {'time_in':cuts.frame_in / framerate, 'time_out': cuts.frame_out / framerate, "asset": asset_id, \
                                'id': str(cuts.id), 'object': [], 'ocr': "", 'stt': "", "contact": [], "emotion": [], "shots": [], "location": [], "title": video_title, "content_type":content_type}}
                cut_objects = [x['words'].upper().strip() for x in FrameTag.objects.filter(video__id=video_id, tag__parent__title__iexact="Others").filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("words").distinct() if x['words']]
                if cut_objects:
                    index_dict['_source']['object'].extend(cut_objects)
                index_list.append(index_dict)
    if index_list:
        helpers.bulk(es, index_list)

def index_shots(video_id):
    video = Video.objects.filter(id=video_id).first()
    index_list = []
    if video:
        framerate = int(video.frame_rate)
        video_id = str(video.id)
        video_cuts = ManualTag.objects.filter(video=video_id).order_by('frame_in')
        asset = AssetVersion.objects.filter(video=video_id).first()
        asset_id = asset.id
        video_title = video.title
        content_type = asset.content_type.id
        for cuts in video_cuts:
            cuts_id = str(cuts.id)
            doc = get_document(cuts_id)
            if doc:
                doc['shots'] = []
                cut_tags = cuts.tags.filter(tags__parent__title__iexact="Shots")
                if cut_tags:
                    for tag in cut_tags:
                        doc['shots'].append("{} {}".format(tag.title.upper(), tag.parent.title.upper()))
                update_document(cuts_id, doc)
            else:
                index_dict = {"_id": str(cuts.id) ,"_index": "asearch", "_type": "docs", "_source": {'time_in':cuts.frame_in / framerate, 'time_out': cuts.frame_out / framerate, "asset": asset_id, \
                                'id': str(cuts.id), 'object': [], 'ocr': "", 'stt': "", "contact": [], "emotion": [], "shots": [], "location": [], "title": video_title, "content_type":content_type}}
                cut_tags = cuts.tags.filter(tags__parent__title__iexact="Shots")
                if cut_tags:
                    for tag in cut_tags:
                        index_dict['_source']['shots'].append("{} {}".format(tag.title.upper(), tag.parent.title.upper()))
                index_list.append(index_dict)
    if index_list:
        helpers.bulk(es, index_list)

def index_ocr(video_id):
    video = Video.objects.filter(id=video_id).first()
    index_list = []
    if video:
        framerate = int(video.frame_rate)
        video_id = str(video.id)
        video_cuts = ManualTag.objects.filter(video=video_id).order_by('frame_in')
        asset = AssetVersion.objects.filter(video=video_id).first()
        asset_id = asset.id
        video_title = video.title
        content_type = asset.content_type.id
        for cuts in video_cuts:
            cuts_id = str(cuts.id)
            doc = get_document(cuts_id)
            if doc:
                doc['ocr'] = []
                ocr_tags = [x['words'] for x in OCRTag.objects.filter(video__id=video_id).filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("words").distinct()]
                if ocr_tags:
                    doc['ocr'] = " ".join(ocr_tags).replace("\n", '')
                update_document(cuts_id, doc)
            else:
                index_dict = {"_id": str(cuts.id) ,"_index": "asearch", "_type": "docs", "_source": {'time_in':cuts.frame_in / framerate, 'time_out': cuts.frame_out / framerate, "asset": asset_id, \
                                'id': str(cuts.id), 'object': [], 'ocr': "", 'stt': "", "contact": [], "emotion": [], "shots": [], "location": [], "title": video_title, "content_type":content_type}}
                ocr_tags = [x['words'] for x in OCRTag.objects.filter(video__id=video_id).filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("words").distinct()]
                if ocr_tags:
                    index_dict['_source']['ocr'] = " ".join(ocr_tags).replace("\n", '')
                index_list.append(index_dict)
    if index_list:
        helpers.bulk(es, index_list)

def index_stt(video_id):
    video = Video.objects.filter(id=video_id).first()
    index_list = []
    if video:
        framerate = int(video.frame_rate)
        video_id = str(video.id)
        video_cuts = ManualTag.objects.filter(video=video_id).order_by('frame_in')
        asset = AssetVersion.objects.filter(video=video_id).first()
        asset_id = asset.id
        video_title = video.title
        content_type = asset.content_type.id
        for cuts in video_cuts:
            cuts_id = str(cuts.id)
            doc = get_document(cuts_id)
            if doc:
                doc['stt'] = []
                stt_tags = [x['words'] for x in KeywordTag.objects.filter(video__id=video_id, tags__isnull=True).filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("words").distinct()]
                if stt_tags:
                    doc['stt'] = " ".join(stt_tags)
                update_document(cuts_id, doc)
            else:
                index_dict = {"_id": str(cuts.id) ,"_index": "asearch", "_type": "docs", "_source": {'time_in':cuts.frame_in / framerate, 'time_out': cuts.frame_out / framerate, "asset": asset_id, \
                                'id': str(cuts.id), 'object': [], 'ocr': "", 'stt': "", "contact": [], "emotion": [], "shots": [], "location": [], "title": video_title, "content_type":content_type}}
                stt_tags = [x['words'] for x in KeywordTag.objects.filter(video__id=video_id, tags__isnull=True).filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("words").distinct()]
                if stt_tags:
                    index_dict['_source']['ocr'] = " ".join(stt_tags)
                index_list.append(index_dict)
    if index_list:
        helpers.bulk(es, index_list)

@app.task(name='periodic_video_indexing')
def periodic_video_indexing(arg):
    assets = AssetVersion.objects.filter(is_tagged=True, is_indexed=False, video__frame_rate__isnull=False)
    if assets:
        video_list = [str(x.video.id) for x in assets]
        index_videos(video_list)
        assets.update(is_indexed=True)

@app.task
def index_videos(video_list):
    es = Elasticsearch(
    hosts = [{'host': ELASTIC_URL, 'port': 443}],
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
    )

    index_list = []
    videos = Video.objects.filter(id__in=video_list)
    for video in videos:
        framerate = int(video.frame_rate)
        video_id = str(video.id)
        video_cuts = ManualTag.objects.filter(video=video_id).order_by('frame_in')
        asset = AssetVersion.objects.filter(video=video_id).first()
        asset_id = asset.id
        video_title = video.title
        content_type = asset.content_type.id
        for cuts in video_cuts:

            # default dictionary for saving to elastic
            index_dict = {"_id": str(cuts.id) ,"_index": "asearch", "_type": "docs", "_source": {'time_in':cuts.frame_in / framerate, 'time_out': cuts.frame_out / framerate, "asset": asset_id, 'id': str(cuts.id), 'object': [], 'ocr': "", 'stt': "", "contact": [], "emotion": [], "shots": [], "location": [], "title": video_title, "content_type":content_type}}

            #Object Tags
            cut_tags = cuts.tags.filter(tags__parent__title__iexact="Shots")
            if cut_tags:
                for tag in cut_tags:
                    index_dict['_source']['shots'].append("{} {}".format(tag.title.upper(), tag.parent.title.upper()))
            cut_objects = [x['words'].upper().strip() for x in FrameTag.objects.filter(video__id=video_id, tag__parent__title__iexact="Others").filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("words").distinct() if x['words']]
            if cut_objects:
                index_dict['_source']['object'].extend(cut_objects)

            #OCR tags
            ocr_tags = [x['words'] for x in OCRTag.objects.filter(video__id=video_id).filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("words").distinct()]
            if ocr_tags:
                index_dict['_source']['ocr'] = " ".join(ocr_tags).replace("\n", '')

            #STT tags
            stt_tags = [x['words'] for x in KeywordTag.objects.filter(video__id=video_id, tags__isnull=True).filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("words").distinct()]
            if stt_tags:
                index_dict['_source']['stt'] = " ".join(stt_tags)

            #Locations
            cut_objects = [x['words'].upper().strip() for x in FrameTag.objects.filter(video__id=video_id, tag__parent__title__iexact="Location").filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("words").distinct() if x['words']]
            if cut_objects:
                index_dict['_source']['location'].extend(cut_objects)
            else:
                cut_tags = cuts.tags.filter(tags__parent__title__iexact="Location")
                if cut_tags:
                    for tag in cut_tags:
                        index_dict['_source']['location'].append("{} {}".format(tag.title.upper()))

            #Emotion Tags:
            emotion_list = [x['emotion_quo'].upper().strip() for x in EmotionTag.objects.filter(video__id=video_id).filter(frame_in__gte=cuts.frame_in, frame_out__lte=cuts.frame_out).values("emotion_quo").distinct() if x['emotion_quo']]
            if not emotion_list:
                emotions = [x['emotion'] for x in Face.objects.filter(face_group__video=video, face_rect__frame__videoframe__time__gte=cuts._seconds_in(), face_rect__frame__videoframe__time__lte=cuts._seconds_out()).values("emotion").distinct() if x['emotion'] != 'neutral']
                emotion_list = [x.replace("happiness", "happy").replace("sadness", 'sad').upper() for x in emotions]
            if emotion_list:
                index_dict['_source']['emotion'].extend(emotion_list)

            #FaceGroup Tags
            person_tags = video.facegroup_set.all()
            for person_tag in person_tags:
                if person_tag.person:
                    timeline = sorted(person_tag.timeline)
                    for times in timeline:
                        if times >= cuts.frame_in / framerate and times <= cuts.frame_out / framerate:
                            index_dict['_source']['contact'].append(person_tag.person.name.upper())
                            break

            index_list.append(index_dict)
    helpers.bulk(es, index_list)

def advanced_search(search_query, content_type):
    search_dict = wit_entity_call(search_query)
    must_list = []
    result_dict = OrderedDict()
    for key in search_dict.keys():
        if search_dict[key]:
            for query in search_dict[key]:
                must_list.append({"match_phrase": {key: query}})
    if must_list:
        query = {
        "query": {
            "bool": {
                "must": must_list
                }
            }
        }
        results = es.search(index='asearch', body=query, size=5000)
        if results['hits']['hits']:
            for result in results['hits']['hits']:
                if result['_source']['content_type'] == content_type:
                    result_dict.setdefault(result['_source']['asset'], []).append({'time_in': result['_source']['time_in'], 'time_out': result['_source']['time_out']})
            return result_dict
        else:
            return result_dict
    else:
        return result_dict

def is_time_stamp(l):
    if l[:2].isnumeric() and l[2] == ':':
        return True
    return False

def has_letters(line):
    if re.search('[a-zA-Z]', line):
        return True
    return False

def has_no_text(line):
    l = line.strip()
    if not len(l):
        return True
    if l.isnumeric():
        return True
    if is_time_stamp(l):
        return True
    if l[0] == '(' and l[-1] == ')':
        return True
    if not has_letters(line):
        return True
    return False

def is_lowercase_letter_or_comma(letter):
    if letter.isalpha() and letter.lower() == letter:
        return True
    if letter == ',':
        return True
    return False

def clean_up(lines):
    """
    Get rid of all non-text lines and
    try to combine text broken into multiple lines
    """
    new_lines = []
    for line in lines[0:]:
        if has_no_text(line):
            continue
        elif len(new_lines) and is_lowercase_letter_or_comma(line[0]):
            new_lines[-1] = new_lines[-1].strip() + ' ' + line
        else:
            new_lines.append(line)
    return new_lines

def clean_text(file_name):
    file_name = file_name
    file_encoding = 'utf-8'
    with open(file_name, encoding=file_encoding, errors='replace') as f:
        lines = f.readlines()
        new_lines = clean_up(lines)
    new_file_name = '/tmp/subtitles/text.txt'
    with open(new_file_name, 'w') as f:
        for line in new_lines:
            line = re.sub(r'<.+?>', '', line)
            line = re.sub(r'{.+?}', '', line)
            line = line.lower()
            line = re.sub(r"[^\w\d'\s]+",'',line)
            f.write(line.strip()+ '\n')

@periodic_task(run_every=crontab(minute=0, hour='19'))
def update_fingerrpints_tag():
    bulk_update_fingerprints()
    fetch_playout()

@app.task
def fetch_subtitles(file_name):
    check_or_create_file("/tmp/subtitles/")
    try:
        video = subliminal.Video.fromname(file_name)
    except ValueError:
        return None
    best_subtitles = subliminal.download_best_subtitles([video], {Language('eng')})
    if best_subtitles[video]:
        best_subtitle = best_subtitles[video][0]
        subliminal.save_subtitles(video, [best_subtitle], directory='/tmp/subtitles/')
        clean_text("/tmp/subtitles/{}".format(file_name.split(".")[0] + '.en.srt'))
        lines = [x for x in open('/tmp/subtitles/text.txt')]
        shutil.rmtree('/tmp/subtitles/')
        return lines
    else:
        shutil.rmtree('/tmp/subtitles/')
        return None

@app.task
def set_unfinished_job_status():
    batch = Batch.objects.order_by('last_created_on').last()
    ob_video_processing_status = VideoProcessingStatus.objects.filter(batch=batch, processed=False)
    jobs_stuck = []
    for i in ob_video_processing_status:
        video_ob = i.video
        tmp_auto_jobs = AutoVideoJob.objects.filter(video=video_ob, job_status= "PRO")
        for j in tmp_auto_jobs:
            jobs_stuck.append(j)
    for i in jobs_stuck:
        i.job_status = "FAI"
        i.save()

@app.task
def rerun_unfinished_job():
    batch = Batch.objects.order_by('last_created_on').last()
    ob_video_processing_status = VideoProcessingStatus.objects.filter(batch=batch, processed=False)
    jobs_stuck = []

    for i in ob_video_processing_status:
        video_ob = i.video
        tmp_auto_jobs = AutoVideoJob.objects.filter(video=video_ob, job_status= "PRO")
        for j in tmp_auto_jobs:
            jobs_stuck.append(j)

    def process_for_instance(instance):
    # if kwargs.get('created'):
        logger.debug('We are here')
        logger.debug(instance.job_type.name)
        video_instance = instance.video

        #append this to tasks downloading tmp video file. Incase of failure of task we need to delete the video downloaded
        # and will provide a path to the same.
        tmp_file_name = os.path.join('/tmp/videos/', str(uuid.uuid4())+'.mp4')

        if instance.job_type.name == 'Compliance':
            FrameTag.objects.filter(video=video_instance, created_by=None).delete()
            KeywordTag.objects.filter(video=video_instance, created_by=None).delete()
            background_compliance_video.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name=None)
            background_compliance_audio.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name= None)

        if instance.job_type.name == 'Identify Objects':
            logger.debug('we are starting clearing')
            FrameTag.objects.filter(video=video_instance, created_by=None).delete()
            background_video_processing.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name)

        elif instance.job_type.name == 'Identify Faces' :
            background_video_processing_face_detection.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name)

        elif instance.job_type.name == "Identify Emotion":
            backgroundprocess_emotion.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name)

        elif instance.job_type.name == 'Identify Trivia':
            background_video_processing_trivia.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name)

        elif instance.job_type.name == 'Match Faces':
            backgroudprocess_match_face.delay(video_instance.id, instance.id)

        elif instance.job_type.name == 'Find Keywords Hindi':
            backgroundprocess_keywords.delay(video_instance.file, video_instance.id, instance.id, 'hi-IN', tmp_file_name)

        elif instance.job_type.name == 'Find Keywords English With Sentiment':
            backgroundprocess_sentiment.delay(video_instance.file, video_instance.id, instance.id, 'en-IN', tmp_file_name)

        elif instance.job_type.name == 'Find Keywords Hindi With Sentiment':
            backgroundprocess_sentiment.delay(video_instance.file, video_instance.id, instance.id, 'hi-IN', tmp_file_name)

        elif instance.job_type.name == 'Find Keywords Marathi With Sentiment':
            backgroundprocess_sentiment.delay(video_instance.file, video_instance.id, instance.id, 'mr-IN', tmp_file_name)

        elif instance.job_type.name == 'Generate Hardcuts':
            background_video_processing_hardcuts.delay(video_instance.file, video_instance.id, instance.id, tmp_file_name)

        elif instance.job_type.name == 'Find Keywords':
            backgroundprocess_keywords.delay(video_instance.file, video_instance.id, instance.id, 'en-US', tmp_file_name)

        elif instance.job_type.name == "Detect Text":
            background_detect_text.delay(video_instance.file, video_instance.id, instance.id, None, None, 'en', tmp_file_name, tmp_file_name=tmp_file_name)

        else:
            pass

    for i in jobs_stuck:
        process_for_instance(i)


@app.task
def send_ingest_report(id, date_range, channel=None, username=None, content_type=None, type="ingest"):
    start_date, end_date= date_range.split(",")
    mast_report_gen = MasterReportGen.objects.filter(id=id).first()
    mast_report_gen.status = 'PRG'
    mast_report_gen.save()

    user = User.objects.filter(username__iexact=username).first()
    # try:
    content_type = ContentType.objects.all().filter(id=str(content_type)).first()
    data_report = []

    if channel:
        channel = channel.split(",")
    else:
        channel = Channel.objects.all()

    if content_type.model == "promo":
        qs = Promo.objects.filter(channel__in = channel, created_on__date__gte = start_date, created_on__date__lte = end_date)
    else:
        qs = Rushes.objects.filter(channel__in = channel, created_on__date__gte = start_date, created_on__date__lte = end_date)

    def get_ingest_date(nbm):
        if nbm:
            return nbm.split("/")[5]
        else:
            return "NOT AVAILABLE"

    for x in qs:
        asset_version =  AssetVersion.objects.filter(object_id = x.id, proxy_type="SRC").first()
        if asset_version:
            video_proxy_ob = asset_version.video.metadata
            if video_proxy_ob is None:
                video_proxy_ob_title = None
                video_proxy_ob_nbm = None
                video_proxy_ob_nbm_storage_status = None
            else:
                video_proxy_ob_title = video_proxy_ob.title
                video_proxy_ob_nbm = video_proxy_ob.nbm
                video_proxy_ob_nbm_storage_status = video_proxy_ob.nbm_storage_status

            data = [x.created_on.date(), x.ingested_on, video_proxy_ob_title, asset_version.material_id, video_proxy_ob_nbm, video_proxy_ob_nbm_storage_status, asset_version.video.size, asset_version.video.duration]
            data_report.append(data)
        else:
            data = 8*[None]
            data_report.append(data)
    df = pd.DataFrame(data_report)
    if not df.empty:
        df.columns = (['Creation Date', 'Ingest Date', 'Media Title', 'MAT ID', 'NBM path', 'NBM Status', 'File size', 'Duration'])
    else:
        df = pd.DataFrame(columns=(['Creation Date', 'Ingest Date', 'Media Title', 'MAT ID', 'NBM path', 'NBM Status', 'File size', 'Duration']))

    if type == "editor":
        df = df.drop(['NBM path','File size', 'Creation Date'], axis=1)

    df.to_csv("/tmp/{}.csv".format(id), index=False)
    mast_report_gen.status = 'RDY'
    mast_report_gen.save()
    # except:
    #     mast_report_gen.status = 'FAI'
    #     mast_report_gen.save()

class Timecode(object):
    """The main timecode class.
    Does all the calculation over frames, so the main data it holds is
    frames, then when required it converts the frames to a timecode by
    using the frame rate setting.
    :param framerate: The frame rate of the Timecode instance. It
      should be one of ['23.976', '23.98', '24', '25', '29.97', '30', '50',
      '59.94', '60', 'NUMERATOR/DENOMINATOR', ms'] where "ms" equals to
      1000 fps.
      Can not be skipped.
      Setting the framerate will automatically set the :attr:`.drop_frame`
      attribute to correct value.
    :param start_timecode: The start timecode. Use this to be able to
      set the timecode of this Timecode instance. It can be skipped and
      then the frames attribute will define the timecode, and if it is also
      skipped then the start_second attribute will define the start
      timecode, and if start_seconds is also skipped then the default value
      of '00:00:00:00' will be used.
      When using 'ms' frame rate, timecodes like '00:11:01.040' use '.040'
      as frame number. When used with other frame rates, '.040' represents
      a fraction of a second. So '00:00:00.040'@25fps is 1 frame.
    :type framerate: str or int or float or tuple
    :type start_timecode: str or None
    :param start_seconds: A float or integer value showing the seconds.
    :param int frames: Timecode objects can be initialized with an
      integer number showing the total frames.
    """

    def __init__(self, framerate, start_timecode=None, start_seconds=None,
                 frames=None):
        self.drop_frame = False
        self.ms_frame = False
        self.fraction_frame = False
        self._int_framerate = None
        self._framerate = None
        self.framerate = framerate

        self.frames = None

        # attribute override order
        # start_timecode > frames > start_seconds
        if start_timecode:
            self.frames = self.tc_to_frames(start_timecode)
        else:
            if frames is not None:  # because 0==False, and frames can be 0
                self.frames = frames
            elif start_seconds is not None:
                if start_seconds == 0:
                    raise ValueError("``start_seconds`` argument can not be 0")
                self.frames = self.float_to_tc(start_seconds)
            else:
                # use default value of 00:00:00:00
                self.frames = self.tc_to_frames('00:00:00:00')

    @property
    def framerate(self):
        """getter for _framerate attribute
        """
        return self._framerate

    @framerate.setter
    def framerate(self, framerate):  # lint:ok
        """setter for the framerate attribute
        :param framerate:
        :return:
        """

        # Convert rational frame rate to float
        numerator = None
        denominator = None

        try:
            if '/' in framerate:
                numerator, denominator = framerate.split('/')
        except TypeError:
            # not a string
            pass

        if isinstance(framerate, tuple):
            numerator, denominator = framerate

        if numerator and denominator:
            framerate = round(float(numerator) / float(denominator), 2)

            if framerate.is_integer():
                framerate = int(framerate)

        # check if number is passed and if so convert it to a string
        if isinstance(framerate, (int, float)):
            framerate = str(framerate)

        # set the int_frame_rate
        if framerate == '29.97':
            self._int_framerate = 30
            self.drop_frame = True
        elif framerate == '59.94':
            self._int_framerate = 60
            self.drop_frame = True
        elif framerate in ['23.976', '23.98']:
            framerate = '24'
            self._int_framerate = 24
        elif framerate in ['ms', '1000']:
            self._int_framerate = 1000
            self.ms_frame = True
            framerate = 1000
        elif framerate == 'frames':
            self._int_framerate = 1
        else:
            self._int_framerate = int(float(framerate))

        self._framerate = framerate

    def set_fractional(self, state):
        """Set or unset timecode to be represented with fractional seconds
        :param bool state:
        """
        self.fraction_frame = state

    def set_timecode(self, timecode):
        """Sets the frames by using the given timecode
        """
        self.frames = self.tc_to_frames(timecode)

    def float_to_tc(self, seconds):
        """set the frames by using the given seconds
        """
        return int(seconds * self._int_framerate)

    def tc_to_frames(self, timecode):
        """Converts the given timecode to frames
        """
        hours, minutes, seconds, frames = map(int,
                                              self.parse_timecode(timecode)
                                              )

        if isinstance(timecode, int):
            time_tokens = [hours, minutes, seconds, frames]
            timecode = ':'.join(str(t) for t in time_tokens)

            if self.drop_frame:
                timecode = ';'.join(timecode.rsplit(':', 1))

        ffps = float(self._framerate)

        if self.drop_frame:
            # Number of drop frames is 6% of framerate rounded to nearest
            # integer
            drop_frames = int(round(ffps * .066666))
        else:
            drop_frames = 0

        # We don't need the exact framerate anymore, we just need it rounded to
        # nearest integer
        ifps = self._int_framerate

        # Number of frames per hour (non-drop)
        hour_frames = ifps * 60 * 60

        # Number of frames per minute (non-drop)
        minute_frames = ifps * 60

        # Total number of minutes
        total_minutes = (60 * hours) + minutes

        # Handle case where frames are fractions of a second
        if len(timecode.split('.')) == 2 and not self.ms_frame:
            self.fraction_frame = True
            fraction = timecode.rsplit('.', 1)[1]

            frames = int(round(float('.' + fraction) * ffps))

        frame_number = \
            ((hour_frames * hours) + (minute_frames * minutes) +
             (ifps * seconds) + frames) - \
            (drop_frames * (total_minutes - (total_minutes // 10)))

        frames = frame_number + 1

        return frames

    def frames_to_tc(self, frames):
        """Converts frames back to timecode
        :returns str: the string representation of the current time code
        """
        ffps = float(self._framerate)

        if self.drop_frame:
            # Number of frames to drop on the minute marks is the nearest
            # integer to 6% of the framerate
            drop_frames = int(round(ffps * .066666))
        else:
            drop_frames = 0

        # Number of frames in an hour
        frames_per_hour = int(round(ffps * 60 * 60))
        # Number of frames in a day - timecode rolls over after 24 hours
        frames_per_24_hours = frames_per_hour * 24
        # Number of frames per ten minutes
        frames_per_10_minutes = int(round(ffps * 60 * 10))
        # Number of frames per minute is the round of the framerate * 60 minus
        # the number of dropped frames
        frames_per_minute = int(round(ffps) * 60) - drop_frames

        frame_number = frames - 1

        if frame_number < 0:
            # Negative time. Add 24 hours.
            frame_number += frames_per_24_hours

        # If frame_number is greater than 24 hrs, next operation will rollover
        # clock
        frame_number %= frames_per_24_hours

        if self.drop_frame:
            d = frame_number // frames_per_10_minutes
            m = frame_number % frames_per_10_minutes
            if m > drop_frames:
                frame_number += (drop_frames * 9 * d) + \
                    drop_frames * ((m - drop_frames) // frames_per_minute)
            else:
                frame_number += drop_frames * 9 * d

        ifps = self._int_framerate

        frs = frame_number % ifps
        if self.fraction_frame:
            frs = round(frs / float(ifps), 3)

        secs = (frame_number // ifps) % 60
        mins = ((frame_number // ifps) // 60) % 60
        hrs = (((frame_number // ifps) // 60) // 60)

        return hrs, mins, secs, frs

    def tc_to_string(self, hrs, mins, secs, frs):
        if self.fraction_frame:
            return "{hh:02d}:{mm:02d}:{ss:06.3f}".format(hh=hrs,
                                                         mm=mins,
                                                         ss=secs + frs
                                                         )

        ff = "%02d"
        if self.ms_frame:
            ff = "%03d"

        return ("%02d:%02d:%02d%s" + ff) % (hrs,
                                            mins,
                                            secs,
                                            self.frame_delimiter,
                                            frs)

    @classmethod
    def parse_timecode(cls, timecode):
        """parses timecode string NDF '00:00:00:00' or DF '00:00:00;00' or
        milliseconds/fractionofseconds '00:00:00.000'
        """
        if isinstance(timecode, int):
            indices = range(2, 10, 2)
            hrs, mins, secs, frs = [hex(timecode)[i:i + 2] for i in indices]

        else:
            bfr = timecode.replace(';', ':').replace('.', ':').split(':')
            hrs = int(bfr[0])
            mins = int(bfr[1])
            secs = int(bfr[2])
            frs = int(bfr[3])

        return hrs, mins, secs, frs

    @property
    def frame_delimiter(self):
        """Return correct symbol based on framerate."""
        if self.drop_frame:
            return ';'

        elif self.ms_frame or self.fraction_frame:
            return '.'

        else:
            return ':'

    def __iter__(self):
        return self

    def next(self):
        self.add_frames(1)
        return self

    def back(self):
        self.sub_frames(1)
        return self

    def add_frames(self, frames):
        """adds or subtracts frames number of frames
        """
        self.frames += frames

    def sub_frames(self, frames):
        """adds or subtracts frames number of frames
        """
        self.add_frames(-frames)

    def mult_frames(self, frames):
        """multiply frames
        """
        self.frames *= frames

    def div_frames(self, frames):
        """adds or subtracts frames number of frames"""
        self.frames = self.frames / frames

    def __eq__(self, other):
        """the overridden equality operator
        """
        if isinstance(other, Timecode):
            return self._framerate == other._framerate and \
                self.frames == other.frames
        elif isinstance(other, str):
            new_tc = Timecode(self._framerate, other)
            return self.__eq__(new_tc)
        elif isinstance(other, int):
            return self.frames == other

    def __ge__(self, other):
        """override greater or equal to operator"""
        if isinstance(other, Timecode):
            return self._framerate == other._framerate and \
                self.frames >= other.frames
        elif isinstance(other, str):
            new_tc = Timecode(self._framerate, other)
            return self.frames >= new_tc.frames
        elif isinstance(other, int):
            return self.frames >= other

    def __gt__(self, other):
        """override greater operator"""
        if isinstance(other, Timecode):
            return self._framerate == other._framerate and \
                self.frames > other.frames
        elif isinstance(other, str):
            new_tc = Timecode(self._framerate, other)
            return self.frames > new_tc.frames
        elif isinstance(other, int):
            return self.frames > other

    def __le__(self, other):
        """override less or equal to operator"""
        if isinstance(other, Timecode):
            return self._framerate == other._framerate and \
                self.frames <= other.frames
        elif isinstance(other, str):
            new_tc = Timecode(self._framerate, other)
            return self.frames <= new_tc.frames
        elif isinstance(other, int):
            return self.frames <= other

    def __lt__(self, other):
        """override less operator"""
        if isinstance(other, Timecode):
            return self._framerate == other._framerate and \
                self.frames < other.frames
        elif isinstance(other, str):
            new_tc = Timecode(self._framerate, other)
            return self.frames < new_tc.frames
        elif isinstance(other, int):
            return self.frames < other

    def __add__(self, other):
        """returns new Timecode instance with the given timecode or frames
        added to this one
        """
        # duplicate current one
        tc = Timecode(self._framerate, frames=self.frames)

        if isinstance(other, Timecode):
            tc.add_frames(other.frames)
        elif isinstance(other, int):
            tc.add_frames(other)
        else:
            raise TimecodeError(
                'Type %s not supported for arithmetic.' %
                other.__class__.__name__
            )

        return tc

    def __sub__(self, other):
        """returns new Timecode instance with subtracted value"""
        if isinstance(other, Timecode):
            subtracted_frames = self.frames - other.frames
        elif isinstance(other, int):
            subtracted_frames = self.frames - other
        else:
            raise TimecodeError(
                'Type %s not supported for arithmetic.' %
                other.__class__.__name__
            )

        return Timecode(self._framerate, frames=subtracted_frames)

    def __mul__(self, other):
        """returns new Timecode instance with multiplied value"""
        if isinstance(other, Timecode):
            multiplied_frames = self.frames * other.frames
        elif isinstance(other, int):
            multiplied_frames = self.frames * other
        else:
            raise TimecodeError(
                'Type %s not supported for arithmetic.' %
                other.__class__.__name__
            )

        return Timecode(self._framerate, frames=multiplied_frames)

    def __div__(self, other):
        """returns new Timecode instance with divided value"""
        if isinstance(other, Timecode):
            div_frames = self.frames / other.frames
        elif isinstance(other, int):
            div_frames = self.frames / other
        else:
            raise TimecodeError(
                'Type %s not supported for arithmetic.' %
                other.__class__.__name__
            )

        return Timecode(self._framerate, frames=div_frames)

    def __repr__(self):
        return self.tc_to_string(*self.frames_to_tc(self.frames))

    @property
    def hrs(self):
        hrs, mins, secs, frs = self.frames_to_tc(self.frames)
        return hrs

    @property
    def mins(self):
        hrs, mins, secs, frs = self.frames_to_tc(self.frames)
        return mins

    @property
    def secs(self):
        hrs, mins, secs, frs = self.frames_to_tc(self.frames)
        return secs

    @property
    def frs(self):
        hrs, mins, secs, frs = self.frames_to_tc(self.frames)
        return frs

    @property
    def frame_number(self):
        """returns the 0 based frame number of the current timecode instance
        """
        return self.frames - 1

    @property
    def float(self):
        """returns the seconds as float
        """
        return self.frames / float(self.framerate)

class TimecodeError(Exception):
    """Raised when an error occurred in timecode calculation
    """
    pass

def format_string(count_str=None, time_in_str=None, time_out_str=None, start_timecode_str=None, end_timecode_str=None, line=None, path=""):
    if line == 1:
        return count_str + "  AX       AA/V  C        " + time_in_str + " " + time_out_str + " " + start_timecode_str + " " + end_timecode_str
    if line == 2:
        return "* FROM CLIP NAME: " + path
    if line == 3:
        return "* COMMENTS: " + path
    if line == 4:
        return count_str + "  BL       AA/V  C        " + time_in_str + " " + time_out_str + " " + start_timecode_str + " " + end_timecode_str

def convert_timedelta(time):
    try:
        duration = datetime.timedelta(seconds=time)
    except:
        duration = time
    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    a = "{0:02}".format(hours) + ":{0:02}".format(minutes) + ":{0:02}".format(seconds) + ":{0:02}".format(duration.microseconds)[:3]
    print(a)
    return [a, duration]

def frames_to_timecode(total_frames, frame_rate, drop=None):
    """
    Method that converts frames to SMPTE timecode.

    :param total_frames: Number of frames
    :param frame_rate: frames per second
    :param drop: true if time code should drop frames, false if not
    :returns: SMPTE timecode as string, e.g. '01:02:12:32' or '01:02:12;32'
    """
    if drop and frame_rate not in [29.97, 59.94]:
        raise NotImplementedError("Time code calculation logic only supports drop frame "
                                  "calculations for 29.97 and 59.94 fps.")

    # round fps to the nearest integer
    # note that for frame rates such as 29.97 or 59.94,
    # we treat them as 30 and 60 when converting to time code
    # then, in some cases we 'compensate' by adding 'drop frames',
    # e.g. jump in the time code at certain points to make sure that
    # the time code calculations are roughly right.
    fps_int = int(round(frame_rate))

    if drop:
        # drop-frame-mode
        # add two 'fake' frames every minute but not every 10 minute
        # calculate number of drop frames for a 29.97 std NTSC
        # workflow. Here there are 30*60 = 1800 frames in one
        # minute

        FRAMES_IN_ONE_MINUTE = 1800 - 2

        FRAMES_IN_TEN_MINUTES = (FRAMES_IN_ONE_MINUTE * 10) - 2

        ten_minute_chunks = total_frames / FRAMES_IN_TEN_MINUTES
        one_minute_chunks = total_frames % FRAMES_IN_TEN_MINUTES

        ten_minute_part = 18 * ten_minute_chunks
        one_minute_part = 2 * ((one_minute_chunks - 2) / FRAMES_IN_ONE_MINUTE)

        if one_minute_part < 0:
            one_minute_part = 0

        # add extra frames
        total_frames += ten_minute_part + one_minute_part

        # for 60 fps drop frame calculations, we add twice the number of frames
        if fps_int == 60:
            total_frames = total_frames * 2

        # time codes are on the form 12:12:12;12
        smpte_token = ";"

    else:
        # time codes are on the form 12:12:12:12
        smpte_token = ":"

    # now split our frames into time code
    hours = int(total_frames / (3600 * fps_int))
    minutes = int(total_frames / (60 * fps_int) % 60)
    seconds = int(total_frames / fps_int % 60)
    frames = int(total_frames % fps_int)
    return "%02d:%02d:%02d%s%02d" % (hours, minutes, seconds, smpte_token, frames)

@app.task
def generate_edl(id, videos, collection=None, type_='Compliance', is_indexed=True, username=None):
    def comment_on_tagbasis(obj):
        frame_tag_ctype = ContentType.objects.get_for_model(obj).model
        #print(frame_tag_ctype)
        if frame_tag_ctype == 'frametag' and obj.tag.title == 'Comment':
            print("frame_tag comment")
            return obj.comment
        else:
            return obj.words

    # def get_moderation_tags(video, query, filter_list):
    #     compliance_tags = list(video.frametag.all().filter(query).order_by("frame_in"))
    #     keyword_tags = list(video.keywords.all().filter(tags__name="Profanity").order_by('frame_in'))
    #     moderation_tags = compliance_tags + keyword_tags
    #     return moderation_tags

    def get_tags_list(type_, is_indexed, collection, videos):
        ob= []
        videos = videos.split(",")
        # if type_ == 'Compliance':
        #     with open("./utils/moderation.txt", 'r') as fd:
        #         filter_list = [f.strip() for f in fd.readlines()]
        #     query = reduce(operator.or_, (Q(tag__title__icontains=item)&Q(collection=None)&Q(index=None) for item in filter_list))
        #     ob = []
        #     for i in videos: #loop to get tags for every video
        #         i = Video.objects.filter(id = i).first()
        #         ob = ob + get_moderation_tags(i, query, filter_list)
        tag_types_list = compliance_tags
        # elif type_ == 'Programming' and is_indexed == False and len(videos) == 1:
        ob = list(FrameTag.objects.filter(video__in=videos, collection=None, index__isnull=True, tag__parent__title__in=tag_types_list, is_approved=True).order_by('frame_in'))

        # elif type_ == 'Programming' and is_indexed == True and len(videos) == 1:
        #     ob = list(FrameTag.objects.filter(video__in=videos, collection=None, index__isnull=False, tag__parent__title='Programming', is_approved=True).order_by('index'))

        # elif type_ == 'Programming' and is_indexed == True and len(videos) > 1:
        #     ob = list(FrameTag.objects.filter(video__in=videos, collection=collection, index__isnull=False, tag__parent__title='Programming', is_approved=True).order_by('index'))

        return ob
    def slot_in_edl(count, time_in, time_out, obj, f, dataframe_arr, tagged):  
        count_str = "{0:03d}".format(count)  
        time_in_ob = frames_to_timecode(time_in, 25)  
        time_out_ob = frames_to_timecode(time_out, 25)  
        tc1 = Timecode('25', time_in_ob)  
        tc2 = Timecode('25', time_out_ob)  
        delta = tc2 - tc1  
        end_timecode_ob = tc1 + delta  
        time_in_str = str(time_in_ob)  
        time_out_str = str(time_out_ob)  
        start_timecode_str = str(time_in_str)  
        end_timecode_str = str(time_out_str)  
        time_in = time_in/obj.video.frame_rate  
        time_out = time_out/obj.video.frame_rate  
        time_delta_str = str(time_out - time_in)  
        if tagged:
            tmp = format_string(count_str, time_in_str, time_out_str, start_timecode_str, end_timecode_str, 1)
        else:
            tmp = format_string(count_str, time_in_str, time_out_str, start_timecode_str, end_timecode_str, 4) 
        print(tmp)  
        f.write(tmp)  
        f.write("\n")  
        try:
            print(obj.video)
            print(obj.video.id)
            video_path = str(VideoProxyPath.objects.filter(video=obj.video.id).first().nbm)  
        except:  
            video_path = str(Video.objects.filter(id=obj.video.id).first().title)  
        tmp = format_string(count_str, time_in_str, time_out_str, start_timecode_str, end_timecode_str, 2, video_path)  
        print(tmp)  
        f.write(tmp)  
        f.write("\n")  
        if tagged: 
            comment = comment_on_tagbasis(obj)  
            tmp = format_string(line=3,path=comment)  
        else: 
            comment = "" 
            tmp = "" 
        f.write(tmp)  
        f.write("\n\n")  
        dataframe_row = ["{0:03d}".format(count), comment, start_timecode_str, end_timecode_str, time_delta_str, "Comment"]  
        dataframe_arr.append(dataframe_row)

    def single_asset_edl(ob, flle_obj):
        print(Video.objects.filter(id = ob[0].video.id).first().title)
        flle_obj.write("TITLE: {}\n".format(str(Video.objects.filter(id = ob[0].video.id).first().title)))
        flle_obj.write("FCM: NON-DROP FRAME\n\n")
        count  = 1 
        start_timecode = 0 #starttimecode from 1
        dataframe_arr = []
        for i in ob:  
            time_in = i.frame_in  
            time_out = i.frame_out
            frame_rate = i.video.frame_rate
            if(start_timecode != time_in):
                 slot_in_edl(count, start_timecode, time_in, i,flle_obj, dataframe_arr, tagged = 0)  
                 count +=1  
            slot_in_edl(count, time_in, time_out, i, flle_obj, dataframe_arr, tagged = 1)  
            start_timecode = time_out  
            count +=1  
#       f.close() 
        if(len(ob) > 0 and start_timecode != ob[0].video.duration): #for last tag to end of video.
            slot_in_edl(count, start_timecode, ob[0].video.duration*(ob[0].video.frame_rate), ob[0],flle_obj, dataframe_arr, tagged = 0)

        return dataframe_arr   


    mast_report_gen = MasterReportGen.objects.filter(id=id).first()
    mast_report_gen.status = 'PRG'
    mast_report_gen.save()

    f = open("/tmp/EDL.edl","w")
    count =1
    start_timecode_ob = Timecode('25', "00:00:00:00")
    ob = get_tags_list(type_, is_indexed, collection, videos)
    # KeywordTag_ob = list(KeywordTag.objects.filter(video__in=videos,is_approved="ACP"))
    # FrameTag_ob = list(FrameTag.objects.filter(video__in=videos, is_approved="ACP"))
    # ob = KeywordTag_ob + FrameTag_ob
    try:
        if len(videos.split(",")) > 1:
            collection_name = str(Collection.objects.filter(id=collection).first().title)
            f.write("TITLE: {}\n".format(collection_name))
            f.write("FCM: NON-DROP FRAME\n\n")
            dataframe_arr = []
            for obj in ob:
                #print(start_timecode_str)
                count_str = "{0:03d}".format(count)
                time_in_ob = frames_to_timecode(obj.frame_in, 25)
                time_out_ob = frames_to_timecode(obj.frame_out, 25)
                tc1 = Timecode('25', time_in_ob)
                tc2 = Timecode('25', time_out_ob)
                delta = tc2 - tc1
                end_timecode_ob = start_timecode_ob + delta

                ## getting strings
                time_in_str = str(time_in_ob)
                time_out_str = str(time_out_ob)
                start_timecode_str = str(start_timecode_ob)
                end_timecode_str = str(end_timecode_ob)
                ##

                time_in = obj.frame_in/obj.video.frame_rate
                time_out = obj.frame_out/obj.video.frame_rate
                time_delta_str = str(time_out - time_in)

                # time_in = obj.frame_in/obj.video.frame_rate
                # #print(time_in)
                # time_in_str, time_in_ob = convert_timedelta(time_in)
                # time_out = obj.frame_out/obj.video.frame_rate
                # #print(time_out)
                # time_out_str, time_out_ob = convert_timedelta(time_out)
                # time_delta = time_out_ob - time_in_ob
                # time_delta_str, x = convert_timedelta(time_delta)
                # end_timecode = start_timecode_ob + time_delta
                # end_timecode_str, end_timecode_ob = convert_timedelta(end_timecode)
                # start_timecode_str, start_timecode_ob = convert_timedelta(start_timecode_ob)
                tmp = format_string(count_str, time_in_str, time_out_str, start_timecode_str, end_timecode_str, 1)
                print(tmp)
                f.write(tmp)
                f.write("\n")
                try:
                    video_path = str(VideoProxyPath.objects.filter(video=obj.video).first().nbm)
                except:
                    video_path = str(Video.objects.filter(id=video_id).first().title)
                tmp = format_string(count_str, time_in_str, time_out_str, start_timecode_str, end_timecode_str, 2, video_path)
                print(tmp)
                f.write(tmp)
                f.write("\n")
                comment = comment_on_tagbasis(obj)
                tmp = format_string(line=3,path=comment)
                f.write(tmp)
                f.write("\n\n")
                dataframe_row = ["{0:03d}".format(count), comment, start_timecode_str, end_timecode_str, time_delta_str, "Comment"]
                dataframe_arr.append(dataframe_row)
                start_timecode_ob =  end_timecode_ob
                #print(start_timecode)
                #print("-------")
                count += 1

        elif len(videos.split(",")) == 1:
            dataframe_arr = single_asset_edl(ob, f)

        f.close()
        df = pd.DataFrame(dataframe_arr)
        try :
            df.columns = (['Marker Name', 'Description', 'In', 'Out', 'Duration', 'Marker Type'])
        except:
            pass
        df.to_csv("/tmp/EDL-comments.csv", index=False)
        mast_report_gen.status = 'RDY'
        mast_report_gen.save()

    except:
        mast_report_gen.status = 'FAI'
        mast_report_gen.save()

@app.task
def generate_search_edl(id, object_dict):
    mast_report_gen = MasterReportGen.objects.filter(id=id).first()
    mast_report_gen.status = 'PRG'
    mast_report_gen.save()
    print(object_dict)
    print("print the first element")
    print(object_dict[0])
    frame_rate = object_dict[0]['frame_rate'] 
    count =0
    start_timecode_ob = Timecode(str(frame_rate), "00:00:00:00")
    f = open("/tmp/{}.edl".format(id),"w")
    f.write("TITLE: {}\n".format("EDL"))
    f.write("FCM: NON-DROP FRAME\n\n")

    try:
        dataframe_arr = []
        for ob in object_dict: 
            video_id = ob['video'] 
            for time_codes_list in ob['search_times']: 
                print(time_codes_list) 
                frame_in, frame_out = time_codes_list['time_in']*frame_rate, time_codes_list['time_out']*frame_rate 
                count_str = "{0:07d}".format(count) 
                time_in_ob = frames_to_timecode(frame_in, 25) 
                time_out_ob = frames_to_timecode(frame_out, 25) 
                tc1 = Timecode(str(frame_rate), time_in_ob) 
                tc2 = Timecode(str(frame_rate), time_out_ob) 
                delta = tc2 - tc1 
                end_timecode_ob = start_timecode_ob + delta 
                time_in_str = str(time_in_ob) 
                time_out_str = str(time_out_ob) 
                start_timecode_str = str(start_timecode_ob) 
                end_timecode_str = str(end_timecode_ob) 
                time_delta_str = str(frame_out/25 - frame_in/25) 
                tmp = format_string(count_str, time_in_str, time_out_str, start_timecode_str, end_timecode_str, 1) 
                # 'print(tmp) 
                print(tmp)
                f.write(tmp)
                f.write("\n")
                try: 
                    video_path = str(VideoProxyPath.objects.filter(video=video_id).first().nbm) 
                except: 
                    video_path = str(Video.objects.filter(id=video_id).first().title)
                tmp = format_string(count_str, time_in_str, time_out_str, start_timecode_str, end_timecode_str, 2, video_path) 
                print(tmp) 
                f.write(tmp)
                f.write("\n")
                comment = ""
                tmp = format_string(line=3,path=comment)
                f.write(tmp)
                f.write("\n\n")
                dataframe_row = ["{0:03d}".format(count), comment, start_timecode_str, end_timecode_str, time_delta_str, "Comment"]
                dataframe_arr.append(dataframe_row)
                start_timecode_ob =  end_timecode_ob
                  #print(start_timecode)
                  #print("-------")
                count += 1
        f.close()
        df = pd.DataFrame(dataframe_arr)
        try :
            df.columns = (['Marker Name', 'Description', 'In', 'Out', 'Duration', 'Marker Type'])
        except:
            pass
        df.to_csv("/tmp/{}-comments.csv".format(id), index=False)
        mast_report_gen.status = 'RDY'
        mast_report_gen.save()

    except:
        mast_report_gen.status = 'FAI'
        mast_report_gen.save()

# def run_hardcuts(start, end):
#     videos = Video.objects.all().values_list("id", flat=True) 
#     video_hardcuts = AutoVideoJob.objects.filter(job_type__name="Generate Hardcuts", job_status="PRD").values_list("video", flat=True)
#     qs3 = videos.difference(video_hardcuts)
#     new_batch_videos = qs3[start:end]
#     for i in new_batch_videos:
#         instance = Video.objects.filter(id = i).first()
#         job_type_instance_generate_hardcuts, _ = JobType.objects.get_or_create(name='Generate Hardcuts')
#         auto_generate_emotions = AutoVideoJob.objects.create(created_by=None, video=instance,job_type=job_type_instance_generate_hardcuts, eta=0)


    # # users
    # recipients = ["barreto.tony@tessact.com", "akshay.dixit@tessact.com"]
    # # for g in groups.split(","):
    # #     users = User.objects.filter(Q(groups__name=g)).distinct()
    # #     recipients += list(i for i in users.values_list('email', flat=True) if bool(i))
    # # recipients += emails.split(',')
    # recipients_set = set(recipients)
    # recipients_list = list(recipients_set)
    # print(recipients_list)

    # data = [[x["title"], x["nbm"], x["created_on"], x["sourceproxy_upload_status"]] for x in VideoProxyPath.objects.filter(created_on__date__gte = start_date, created_on__date__lte = end_date).values("title", "nbm", "created_on", "sourceproxy_upload_status")]
    # df = pd.DataFrame(data)
    # df.columns = (['File Name', 'File Path', 'Creation Date', 'Status'])
    # file = '/tmp/report.csv'
    # df.to_csv(file)


    # email = EmailMessage(
    #     'Ingest Report for {} to {}'.format(start_date, end_date),
    #     'Please Find attached the ingest-status report file\n\n',
    #     'akshay.dixit@tessact.com',
    #     recipients_list
    # )
    # email.attach_file(file)
    # email.send()
    # time.sleep(15)

def generate_sprite_from_frames(interval, framesPath, columns, rows, size, video_id, offset):
    
    masterWidth = int(100 * columns)
    masterHeight = int(100*(size[1]/size[0]) * rows)

    num_of_images = columns*rows

    dur = int(60 / interval)
    print(dur)
    count = math.ceil(dur/(columns*rows))
    for i in range(count):
        line, column, mode = 0, 0, 'RGBA'
        try:
            finalImage = Image.new(mode=mode, size=(masterWidth, masterHeight), color=(0, 0, 0, 0))
            finalImage.save(os.path.join('/tmp/{}/sprites/'.format(video_id),"sprite{}.png".format(i+offset)))
        except IOError:
            print("IOError")
            mode = 'RGB'
            finalImage = Image.new(mode=mode, size=(masterWidth, masterHeight))

        filesMap = ["out{}.png".format(file_num+1) for file_num in range(i*num_of_images, (i+1)*num_of_images if (i+1)*num_of_images < dur else dur)]
        # print(filesMap)
        for filename in filesMap:
            filepath = os.path.join(framesPath, filename)
            try:
                with Image.open(filepath) as image:
                    l_size = 100, int(100 * size[1]/size[0])
                    # image.thumbnail(l_size, Image.ANTIALIAS)
                    thumb = ImageOps.fit(image, l_size, Image.ANTIALIAS)

                    locationX = l_size[0] * column
                    locationY = l_size[1] * line

                    finalImage.paste(thumb, (locationX, locationY))

                    column += 1

                    if column == columns:
                        line += 1
                        column = 0
            except FileNotFoundError as e:
                print(e)
                column +=1
                if column == columns:
                    line += 1
                    column = 0
                pass

        finalImage.save(os.path.join('/tmp/{}/sprites/'.format(video_id), "sprite{}.png".format(i+offset)))
        print("{} Saved!".format(i+offset))
        return os.path.join('/tmp/{}/sprites/'.format(video_id), "sprite{}.png".format(i+offset))

def generate_video_thumbnail(video, interval, width, height, frames, columns, rows, video_id, offset):
    interval = int(interval)
    size = (width, height)
    file_path = generate_sprite_from_frames(interval, frames, columns, rows, size, video_id, offset)
    return file_path

def make_frames(args, v_file, ss, t, video_id):
    path = os.path.join('/tmp/{}/'.format(video_id),"frames/out%d.png")
    command = [FFMPEG_BIN,
               '-loglevel', 'panic',
               '-ss', str(ss), '-t', str(t),
               '-i', v_file, '-r',
               '1/1', path
               ]
    # b = bash("/opt/bin/ffmpeg -loglevel panic -ss {} -t {} -i {}  -r 1/1 {}".format( ss, t, v_file, os.path.join('/tmp',"frames/out%d.png")))
    output = sp.call(command)
    return os.path.join('/tmp/{}/'.format(video_id),"frames")

def clear_sprites_and_frames(video_id):
    sp.call(['rm', '-r', '{}'.format(os.path.join('/tmp', '{}/'.format(video_id))), '{}'.format(os.path.join('/tmp', '{}.mp4'.format(video_id)))])
    return True

def get_duration(video):

    command = [FFPROBE_BIN,
               '-v', 'error',
               '-show_entries', 
               'format=duration', '-of',
               'default=noprint_wrappers=1:nokey=1',
               video]
    output = sp.check_output(command)
    output = output.decode('utf-8')
    duration = float(output)
    duration = math.ceil(duration/60) 
    print("this is", duration)
    return duration


@app.task
def create_sprites(input_file, video_id):
    if not os.path.exists('/tmp/{}/frames'.format(video_id)):
        os.makedirs('/tmp/{}/frames'.format(video_id))
    if not os.path.exists('/tmp/{}/sprites'.format(video_id)):
        os.makedirs('/tmp/{}/sprites'.format(video_id))
    url = os.path.basename(unquote(input_file))
    url = url.replace('+', ' ')
    args = {}
    tmp_video = '/tmp/{}.mp4'.format(video_id)
    s3.download_file("trigger-uploaded-videos",url, tmp_video)
    duration = get_duration(tmp_video)
    vid = Video.objects.get(id=video_id)
    file = File.objects.get(title=vid.title, url=vid.file)
    channel = 'All' if file.channel == None else file.channel.channel_name 
    for i in range(duration):
        print("Minute {} Starting".format(i))
        make_frames(args, tmp_video, i*60, 60, video_id)
        s_path = generate_video_thumbnail(tmp_video, 1, 384, 288, '/tmp/{}/frames'.format(video_id), 10, 6, video_id, i)
        s3.upload_file(s_path, 'trigger-uploaded-videos', 'sprites/{}/{}/{}'.format(channel, video_id,os.path.basename(s_path)))
    clear_sprites_and_frames(video_id)
    base_url = "https://s3.ap-south-1.amazonaws.com/trigger-uploaded-videos/sprites/{}/{}/sprite{}.png"
    if base_url and video_id and file:
        for i in range(duration):
            s, created = SpriteTag.objects.get_or_create(video=vid, time=i, url=base_url.format(channel, video_id, i))


#creating thumnails

def get_thumbnail(video_id, v_file, ss):
    path = os.path.join('/tmp/thumbnails/','{}.png'.format(video_id))
    command = [FFMPEG_BIN,
               '-v', 'quiet',
               '-i', v_file,
               '-ss', str(ss),
               '-vframes', '1', 
               path]  
    sp.check_output(command)
    size = (42,42)
    file = resize_image(path, size)
    return path

def clear_tmp_thumbnail(video_id):
    sp.call(['rm', '-r', '{}'.format(os.path.join('/tmp/thumbnails/', '{}.png'.format(video_id)))])
    return True

@app.task
def set_thumbnail(video_id, time):
    if not os.path.exists('/tmp/thumbnails/'.format(video_id)):
        os.makedirs('/tmp/thumbnails/'.format(video_id))
    video = Video.objects.get(id=video_id)
    thumbnail_obj = Thumbnail.objects.get(object_id=video_id)
    thumbnail = get_thumbnail(video_id, video.file, time)
    s3.upload_file(thumbnail, 'trigger-uploaded-videos', 'thumbnail/{}.png'.format(video_id))
    clear_tmp_thumbnail(video_id)
    url = "https://s3.ap-south-1.amazonaws.com/trigger-uploaded-videos/thumbnail/{}.png".format(video_id)
    thumbnail_obj.url = url
    thumbnail_obj.save()
    return True

