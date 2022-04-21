#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
#
from __future__ import absolute_import, unicode_literals
from celery import Celery
import subprocess as sp
import re
import os
import uuid
import json
import requests
import errno
import time
import sys
from django.shortcuts import get_object_or_404
from azure.storage.blob import (
    BlockBlobService
)
from docx import Document
from django.conf import settings

from .models import SubtitleSyncJob, ScriptProcessJob

app = Celery('tags')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')


@app.task
def set_frame_tags():
    return True


def check_or_create_file(file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


def sec2tc(sec):
    sign = '-' if sec < 0 else ''
    ms = abs(sec)*1000
    ss, ms = divmod(ms, 1000)
    hh, ss = divmod(ss, 3600)
    mm, ss = divmod(ss, 60)
    TIMECODE_FORMAT = '%s%02d:%02d:%02d,%03d'
    return TIMECODE_FORMAT % (sign, hh, mm, ss, ms)


def generate_srt(obj, dest_path):
    """Generate srt file from a list of dialogues and start and end time"""
    with open(dest_path, 'w+') as srt_fp:
        count = 0
        for dialogue in obj:
            count += 1
            # srt_fp.write('\n')
            srt_fp.write(str(count))
            srt_fp.write('\n')
            start_time = sec2tc(dialogue['start'])
            end_time = sec2tc(dialogue['end'])
            time_line = "{} --> {}".format(start_time, end_time)
            srt_fp.write(time_line)
            srt_fp.write('\n')
            sl = dialogue['sentence'].split('//')
            for l in sl:
                srt_fp.write(l)
                srt_fp.write('\n')
            srt_fp.write('\n')


def clean_gentle(data, dialogues_file):
    sentences = []
    words = []
    for word in data['words']:
        print(word)
        # print("words : {}, start : {}, end : {}".format(word['word'], word['start'], word['end']))
        words.append(word)

    count = 0
    failed_count = 0
    line_count = 0
    last_failed = False
    with open(dialogues_file, 'r+') as dia_fp:
        for line in dia_fp.readlines():
            line_count += 1
            info = {}
            info['sentence'] = line.strip()
            info['start'] = 0
            info['end'] = 0
            for word in re.findall(r"[\w']+", line):
                # print("word : {}".format(word))
                w = words[count]
                if w['case'] == 'success' and w['word'].strip(" ./'-") == word.strip(" ./'-"):
                    # print("words : {}, start : {}, end : {}".format(w['word'], w['start'], w['end']))

                    if word.strip().strip('./-') == w['word']:
                        if info['start'] == 0:
                            if last_failed:
                                info['start'] = sentences[-1]['end']
                            else:
                                info['start'] = w['start']
                            info['end'] = w['end']
                        if info['end'] < w['end']:
                            info['end'] = w['end']
                    count += 1
                elif w['case'] == 'not-found-in-audio' and w['word'].strip(" ./'-") == word.strip(" ./'-"):
                    # print(w)
                    # print('FAIL >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
                    # print(line)
                    # print(re.findall(r"[\w']+", line))
                    count += 1
                    continue
                elif not word.strip(" ./'-"):
                    print('gotcha : {}'.format(word))
                    continue
                else:
                    # Unkown problems immediately fail
                    print(w['word'])
                    print(word)
                    print(re.findall(r"[\w']+", line))
                    sys.exit(0)

            # print("words : {}, start : {}, end : {}".format(info['sentence'].strip(), info['start'], info['end']))
            if info['start'] == 0 or info['end'] == 0:
                try:
                    info['start'] = sentences[-1]['end']
                    info['end'] = float(sentences[-1]['end']) + 2
                    failed_count += 1
                    last_failed = True
                except IndexError:
                    failed_count += 1
                    last_failed = True
            else:
                last_failed = False
            if info['end'] - info['start'] > 3:
                info['start'] = info['end'] - 3
            sentences.append(info)
        print("failed count : {}/{}".format(failed_count, line_count))
    srt_path = os.path.join('/tmp', 'srt', "{}.{}".format(uuid.uuid4(), 'srt'))
    if not os.path.exists(os.path.dirname(srt_path)):
        try:
            os.makedirs(os.path.dirname(srt_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    generate_srt(sentences, srt_path)
    # upload srt to azure
    block_blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME,
                                          account_key=settings.AZURE_ACCOUNT_KEY)
    srt_name = "srt_files/{}.{}".format(uuid.uuid4(), 'srt')
    block_blob_service.create_blob_from_path(settings.AZURE_CONTAINER, srt_name, srt_path)
    full_path = "https://" + settings.AZURE_ACCOUNT_NAME + ".blob.core.windows.net/" + settings.AZURE_CONTAINER + \
                "/" + srt_name
    return full_path


@app.task
def subtitle_sync(subtitle_sync_id):
    job_object = get_object_or_404(SubtitleSyncJob, id=subtitle_sync_id)
    audio_url = job_object.audio_file
    text_url = job_object.transcription
    job_object.job_status = 'PRO'
    job_object.save()
    audio_file_name = audio_url.split('/')[-1]
    audio_path = os.path.join('/tmp', 'audio', audio_file_name)
    # set percent_complete to
    job_object.percent_complete = 0
    job_object.save()
    start_time = time.time()
    if not os.path.isfile(audio_path):
        # create the file
        if not os.path.exists(os.path.dirname(audio_path)):
            try:
                os.makedirs(os.path.dirname(audio_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        r = requests.get(audio_url, stream=True)
        count = 0
        percent_val = 100000000 / float(r.headers['content-length'])
        with open(audio_path, 'wb') as ap:
            for data in r.iter_content(chunk_size=1000000):
                ap.write(data)
                count += 1
                print(int(count * percent_val * 0.2))
                job_object.percent_complete = int(count * percent_val * 0.2)
                job_object.save()
    else:
        # set percent_complete to 20
        # yield 20
        job_object.percent_complete = 20
        job_object.save()

    text_file_name = text_url.split('/')[-1]
    text_path = os.path.join('/tmp', 'text', text_file_name)
    if not os.path.isfile(text_path):
        # create the file
        if not os.path.exists(os.path.dirname(text_path)):
            try:
                os.makedirs(os.path.dirname(text_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        r = requests.get(text_url, stream=True)
        count = 0
        percent_val = max([100000000 / float(r.headers['content-length']), 100])
        with open(text_path, 'wb') as ap:
            for data in r.iter_content(chunk_size=1000000):
                ap.write(data)
                count += 1
    # set percent_complete to 20
    job_object.percent_complete = 20
    job_object.save()
    # gentle file
    gentle_file_name = str(uuid.uuid4()) + '.json'
    gentle_path = os.path.join('/tmp', 'json', gentle_file_name)
    align_path = '/usr/src/app/gentle/align.py'
    cmd = sp.Popen(['python', align_path, str(audio_path), str(text_path)],
                   stderr=sp.STDOUT, stdout=sp.PIPE)
    end_count = 0
    last_time = time.time()
    print("starting processing loop")
    while end_count<2:
        output = cmd.stdout.readline()
        if output == '' and cmd.poll() is not None:
            print("started ended")
            break
        else:
            print("stripped output : {}".format(output.strip()))
            status = output.strip().decode('utf-8').split(':')[-1]
            print("raw status output : {}".format(status))
            prog = re.compile('^[0-9]+\/[0-9]+')
            finish_report = re.compile('([0-9]+) unaligned words \(of ([0-9]+)\)')
            m = prog.match(status)
            r = finish_report.search(status)
            if m:
                print("updating status")
                st = status.split('/')
                # set percent_complete to x
                print(str(int(st[0]) * 80 / int(st[1]) + 20))
                past_percent = job_object.percent_complete
                curr_percent = (int(st[0]) * 80) / int(st[1]) + 20
                job_object.percent_complete = curr_percent
                if curr_percent - past_percent > 0:
                    curr_time = time.time()
                    job_object.eta = ((curr_time-last_time)*(100 - curr_percent)/(curr_percent - past_percent) + job_object.eta)/2
                    last_time = curr_time
                job_object.save()
            elif r:
                print("end report")
                # set percent_complete error rate
                end_count +=1
                print(r.group(0))
    print("out of processing loop")
    rc = cmd.poll()
    j = cmd.stdout.read().decode('utf-8')
    d = json.loads(j)
    srt_path = clean_gentle(d,text_path)
    job_object.job_status = 'PRD'
    job_object.srt_file = srt_path
    job_object.save()


def filter_sentence(txt):
    """filter senteces of formatted content"""
    exp = re.compile('[\(\<][^\(\)\<\>]+[\)\>]')
    m = exp.sub('',txt)
    m = m.replace("\n", ' ').strip()
    return m

@app.task
def script_process(job_id):
    """Process Script files and extract dialogues only"""
    script_process_obj = ScriptProcessJob.objects.get(id=job_id)
    script_process_obj.job_status = 'PRO'
    script_process_obj.save()
    file_path = script_process_obj.script_file
    if file_path.split('.')[-1] == 'docx':
        document = Document(file_path)
        t4 = document.tables[-1]
        rows = t4.rows
        sentences = []
        for row_id in range(rows.len()):
            # process the cell texts
            row = rows[row_id]
            txt = row.cells[2].text
            r1 = row.cells[1].text
            if txt == txt.upper():
                continue
            elif txt == r1:
                continue
            else:
                txt = filter_sentence(txt)
                if txt != '':
                    sentences.append({"txt": txt, "len": len(txt)})
            script_process_obj.percent_complete = (row_id/rows.len())*100
        output_path = os.path.join('/tmp', 'srt', "{}.{}".format(uuid.uuid4(), 'txt'))
        check_or_create_file(output_path)
        with open(output_path, 'w+') as dt:
            for sentence in sentences:
                dt.write(sentence['txt'])
                dt.write('\n')
        block_blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME,
                                              account_key=settings.AZURE_ACCOUNT_KEY)
        txt_name = "txt_files/{}.{}".format(uuid.uuid4(), 'srt')
        block_blob_service.create_blob_from_path(settings.AZURE_CONTAINER, txt_name, output_path)
        full_path = "https://" + settings.AZURE_ACCOUNT_NAME + ".blob.core.windows.net/" + settings.AZURE_CONTAINER + \
                    "/" + txt_name
        script_process_obj.txt_file = full_path
        script_process_obj.job_status = 'PRD'
        script_process_obj.save()
    else:
        raise TypeError('invalid file extension')

