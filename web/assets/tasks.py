from __future__ import absolute_import, unicode_literals
from celery import Celery
import boto3
from .models import RO
import os, shutil
from requests import get
from azure.storage.blob import BlockBlobService

import logging, errno

KEY = 'e80b3b4c298043f8aa6fca9a6e5f343c'  # Replace with a valid subscription key (keeping the quotes in place).

from .file import GroupM, Madison, MadisonViacom, Initiative, Purnima, FCBULKA, SkyStar, HAVAS, StarCom, HRI, DDB, BEI, \
    Zenith, RKSWAMY, PENTAGON, FULCRUM, Vizeum, SPAN
from video.tasks import check_or_create_file, clean_video_file, silentremove

s3_client = boto3.client('s3')

AZURE_ACCOUNT_NAME = 'triggerbackendnormal'
AZURE_ACCOUNT_KEY = 'tadQP8+aFdnxzHBx37KYLoIV92H+Ju9U7a+k1qtwaQDE0tH23qQ7mUUD1qzvXBGd6cGgo7rW4jeA8H6AzXZdPg=='
AZURE_CONTAINER = 'backend-media'

app = Celery('assets')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

logger = logging.getLogger('debug')


def check_or_create_file(file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


def save_to_azure_path(file_path):
    """
    Saves frames images to the azure storage
    :param file_path: source file path
    :return: image_url: url of the image
    """
    block_blob_service = BlockBlobService(account_name=AZURE_ACCOUNT_NAME, account_key=AZURE_ACCOUNT_KEY)
    filename = file_path.split('/')[-1]
    block_blob_service.create_blob_from_path(
        AZURE_CONTAINER,
        os.path.join("ro", filename),
        file_path
    )
    full_path = "https://"+AZURE_ACCOUNT_NAME+".blob.core.windows.net/"+AZURE_CONTAINER+"/"+os.path.join("ro", filename)
    return full_path


def download(url, file_name):
    # open in binary mode
    with open(file_name, "wb") as file:
        # get request
        response = get(url)
        # write to file
        file.write(response.content)


@app.task
def convert(id):
    instance = RO.objects.get(id=id)
    filename = instance.original_file.split('/')[-1]
    file_path = '/tmp/{}'.format(filename)
    download(instance.original_file, file_path)
    if instance.object == "madison":
        r = MadisonViacom(file_path)
    elif instance.object == "madisonviacom":
        r = MadisonViacom(file_path)
    elif instance.object == "groupm":
        r = GroupM(file_path)
    elif instance.object == "mediaedge":
        r = GroupM(file_path)
    elif instance.object == "matrix":
        r = GroupM(file_path)
    elif instance.object == "mediacom":
        r = GroupM(file_path)
    elif instance.object == "initiative":
        r = Initiative(file_path)
    elif instance.object == "purnima":
        r = Purnima(file_path)
    elif instance.object == "fcbulka":
        r = FCBULKA(file_path)
    elif instance.object == "mccan":
        r = FCBULKA(file_path)
    elif instance.object == "dentsu":
        r = FCBULKA(file_path)
    elif instance.object == "skystar":
        r = SkyStar(file_path)
    elif instance.object == "starcom":
        r = StarCom(file_path)
    elif instance.object == "mediavest":
        r = StarCom(file_path)
    elif instance.object == "zenith":
        r = Zenith(file_path)
    elif instance.object == "omnicom":
        r = FCBULKA(file_path)
    elif instance.object == "havas":
        r = HAVAS(file_path)
    elif instance.object == "bei":
        r = BEI(file_path)
    elif instance.object == "ddb":
        r = DDB(file_path)
    elif instance.object == 'hri':
        r = HRI(file_path)
    elif instance.object == 'rkswamy':
        r = RKSWAMY(file_path)
    elif instance.object == 'pentagon':
        r = PENTAGON(file_path)
    elif instance.object == 'vizeum':
        r = Vizeum(file_path)
    elif instance.object == 'span':
        r = SPAN(file_path)
    elif instance.object == 'fulcrum':
        r = FULCRUM(file_path)
    tab = r.get_table('json')
    original_name = os.path.splitext(instance.title)[0]
    logging.error(original_name)
    files = r.generate_output(original_name, instance.dest)
    url = None
    output_filename = None
    if files and len(files) > 1:
        output_filename = '/tmp/{}'.format(original_name)
        shutil.make_archive(output_filename, 'zip', output_filename)
        url = save_to_azure_path(output_filename + ".zip")
    elif files:
        output_filename = files[0]
        url = save_to_azure_path(files[0])
    logging.error(url)
    instance.final_file = url
    instance.process_eta = 1.0
    instance.save()
    instance.advertiser = r.advertiser if r.__getattribute__('advertiser') else ""
    instance.save()
    logger.debug("save complete")
    if '.' in output_filename:
        silentremove(output_filename)
    else:
        silentremove(output_filename + ".zip")