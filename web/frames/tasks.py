#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
#
from __future__ import absolute_import, unicode_literals
from celery import Celery
from contextual.models import Face, FaceGroup, HardCuts
from content.models import PersonGroup, CloudPerson
from urllib.request import urlopen
from PIL import Image
from .models import Frames, Rect
from tags.models import Tag
from tools.core.tools import hardcuts, news_filter, image_to_azure_url
from django.shortcuts import get_object_or_404

import cognitive_face as CF

KEY = 'e80b3b4c298043f8aa6fca9a6e5f343c'  # Replace with a valid subscription key (keeping the quotes in place).
CF.Key.set(KEY)

app = Celery('frames')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

@app.task
def backgroud_face_detection(frame_id):
    frame = Frames.objects.get(id=frame_id)
    if not Face.objects.filter(face_rect__frame=frame):
        imgURL = frame.file
        facesDetected = CF.face.detect(imgURL)
        faceIds = []
        face_tag, created = Tag.objects.get_or_create(name='face')
        j = Image.open(urlopen(imgURL))
        for face in facesDetected:
            faceIds.append(face['faceId'])
            top = face['faceRectangle']['top']
            left = face['faceRectangle']['left']
            width = face['faceRectangle']['width']
            height = face['faceRectangle']['height']
            faceRectObj = Rect.objects.create(x=left, y=top, w=width, h=height, frame=frame)
            faceRectObj.save()
            faceRectObj.tags.add(face_tag)
            faceRectObj.save()
            faceImg = j.crop((left, top, left + width, top + height))
            imgURL = image_to_azure_url(faceImg)
            face_obj = Face.objects.create(azure_face_id=face['faceId'], face_img_url=imgURL, face_rect=faceRectObj)
            face_obj.save()


@app.task
def background_face_grouping():
    faces = Face.objects.all()
    face_ids = faces.values_list('azure_face_id', flat=True)
    similar_faces = CF.face.group(list(face_ids))
    for faceGroup in similar_faces['groups']:
        fg = FaceGroup.objects.create()
        fg.save()
        for face in faceGroup:
            face_obj = get_object_or_404(Face, azure_face_id=face)
            face_obj.face_group = fg
            face_obj.save()


@app.task
def backgroud_face_recon(frame_id):
    frame = Frames.objects.get(id=frame_id)
    pg = PersonGroup.objects.get(title='Royal Family')
    faces = Face.objects.filter(face_rect__frame=frame)
    if not faces:
        imgURL = frame.file
        facesDetected = CF.face.detect(imgURL)
        faceIds = []
        face_tag, created = Tag.objects.get_or_create(name='face')
        j = Image.open(urlopen(imgURL))
        for face in facesDetected:
            faceIds.append(face['faceId'])
            top = face['faceRectangle']['top']
            left = face['faceRectangle']['left']
            width = face['faceRectangle']['width']
            height = face['faceRectangle']['height']
            faceRectObj = Rect.objects.create(x=left, y=top, w=width, h=height, frame=frame)
            faceRectObj.save()
            faceRectObj.tags.add(face_tag)
            faceRectObj.save()
            faceImg = j.crop((left, top, left + width, top + height))
            imgURL = image_to_azure_url(faceImg)
            face_obj = Face.objects.create(azure_face_id=face['faceId'], face_img_url=imgURL, face_rect=faceRectObj)
            face_obj.save()

            result = CF.face.identify([face_obj.azure_face_id], str(pg.id))
            if result[0]['candidates']:
                hit = True
                ci = CloudPerson.objects.get(cloud_id=result[0]['candidates'][0]['personId'])
                fg, created = FaceGroup.objects.get_or_create(person=ci.person)
                face_obj.face_group = fg
                face_obj.save()
    else:
        for face_obj in faces:
            result = CF.face.identify([face_obj.azure_face_id], str(pg.id))
            if result[0]['candidates']:
                ci = CloudPerson.objects.get(cloud_id=result[0]['candidates'][0]['personId'])
                fg, created = FaceGroup.objects.get_or_create(person=ci.person)
                face_obj.face_group = fg
                face_obj.save()
