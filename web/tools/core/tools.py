import subprocess as sp
import json
import numpy
import PIL
import io
import uuid
import datetime
import random
from moviepy.editor import VideoFileClip
import os
import termcolor
import matplotlib.pyplot as plt
import argparse
from azure.storage.blob import BlockBlobService
from azure.storage.blob import ContentSettings
import cognitive_face as CF

KEY = 'e80b3b4c298043f8aa6fca9a6e5f343c'  # Replace with a valid subscription key (keeping the quotes in place).
CF.Key.set(KEY)

AZURE_ACCOUNT_NAME = 'triggerbackendnormal'
AZURE_ACCOUNT_KEY = 'tadQP8+aFdnxzHBx37KYLoIV92H+Ju9U7a+k1qtwaQDE0tH23qQ7mUUD1qzvXBGd6cGgo7rW4jeA8H6AzXZdPg=='
AZURE_CONTAINER = 'backend-media'

FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"

MODE = "info"

FACE_DIR = '/home/tessact/Pictures/Faces'


def time_it(some_function):
    def wrapper(*args, **kwargs):
        start_time = datetime.datetime.now()
        retval = some_function(*args, **kwargs)
        end_time = datetime.datetime.now()
        print("time spent on {} : {}".format(some_function.__name__, end_time - start_time))
        return retval
    return wrapper


@time_it
def total_frames(input_file):
    """
        Get video frame_size
        eg : ffprobe -v error -show_entries stream=nb_read_frames \
              -of default=noprint_wrappers=1
        """
    command = [FFPROBE_BIN,
               '-v', 'error',
               '-select_streams', 'v:0',
               '-show_entries', 'stream=nb_frames',
               '-of', 'default=noprint_wrappers=1',
               '-print_format', 'json',
               input_file]
    output = sp.check_output(command).decode("utf-8", "ignore")
    output = json.loads(output)
    output = output['streams'][0]['nb_frames']
    return output

@time_it
def news_filter(slots):
    filtered_slots = []
    for time_in in slots:
        if not filtered_slots:
            filtered_slots.append(time_in)
        else:
            if time_in - filtered_slots[-1] < 1:
                if len(filtered_slots) > 2:
                    if filtered_slots[-1] - filtered_slots[-2] < 1:
                        filtered_slots.pop()
                        filtered_slots.append(time_in)
                    else:
                        filtered_slots.append(time_in)
                else:
                    filtered_slots.append(time_in)
            else:
                filtered_slots.append(time_in)
    return filtered_slots


@time_it
def hardcuts(input_file):
    """Read video and get histogram of frames"""
    # change the step based on fps
    step = 0.04
    frames = total_frames(input_file)
    slots = []
    fr = 0
    current_frame = None
    myclip = VideoFileClip(input_file)
    mean_limit = 0
    for im in myclip.iter_frames():

        if fr == 0:
            current_frame = im
            shape = current_frame.shape
            print("shape : {}".format(shape))
            mean_limit = shape[0]*shape[1]*0.03
            print("mean_limit : {}".format(mean_limit))
        elif fr != int(frames) - 1:
            # print("i is never 0")
            next_frame = im
            current_time = fr * step
            hist_1, _ = numpy.histogram(current_frame.ravel(), bins=32)
            hist_2, _ = numpy.histogram(next_frame.ravel(), bins=32)
            mean = numpy.mean(numpy.absolute(hist_1 - hist_2))
            if mean > mean_limit:
                slots.append(current_time)
                if MODE == "debug":
                    print(current_time)
                    print(termcolor.colored(mean, "red"))
            current_frame = next_frame
        fr += 1
    return slots


@time_it
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
        os.path.join("frames", filename),
        file_path
    )
    full_path = "https://"+AZURE_ACCOUNT_NAME+".blob.core.windows.net/"+AZURE_CONTAINER+"/"+os.path.join("frames", filename)
    return full_path


def save_to_azure_bytes(byteArr, file_path):
    """
    Saves frames images to the azure storage
    :param file_path: source file path
    :return: image_url: url of the image
    """
    block_blob_service = BlockBlobService(account_name=AZURE_ACCOUNT_NAME, account_key=AZURE_ACCOUNT_KEY)
    filename = file_path.split('/')[-1]
    block_blob_service.create_blob_from_bytes(
        AZURE_CONTAINER,
        os.path.join("frames", filename),
        byteArr
    )
    full_path = "https://"+AZURE_ACCOUNT_NAME+".blob.core.windows.net/"+AZURE_CONTAINER+"/"+os.path.join("frames", filename)
    return full_path


@time_it
def image_to_azure_url(img):
    imgByteArr = io.BytesIO()
    img.save(imgByteArr, format='PNG')
    imgByteArr = imgByteArr.getvalue()
    imgURL = save_to_azure_bytes(imgByteArr, str(uuid.uuid4()) + ".png")
    return imgURL


@time_it
def get_face_ids(input_file, results):
    """
        find faces in every slot of the video by processing two frames in every slot
        :param filtered_slots: This is a array of timestamps where breakage in video flow is detected
        :param input_file: This is the path to the file that is to be processed for face detection
        :param face_img_dest: destination of frame files
        :return: faces_in_slots: This is a dictionary of data containing faces detected in every slot of the video
        """
    # choose 2 images per filtered slots and process for face detection
    current_time = 0
    myclip = VideoFileClip(input_file)
    base_path = os.path.dirname(os.path.dirname(input_file))
    count = 0
    faces = {}
    faceIds = []
    if os.path.isfile(results):
        with open(results, 'r') as fread:
            old_data = json.load(fread)
        faceIds += old_data['faceIds']
        filtered_slots = old_data['hardcuts']
    else:
        slots = hardcuts(input_file)
        filtered_slots = news_filter(slots)

    for slot in filtered_slots:
        slot_time = (random.random() * (slot - current_time) + current_time)
        frame_data = myclip.get_frame(slot_time)
        count += 1
        j = PIL.Image.fromarray(frame_data)
        imgByteArr = io.BytesIO()
        j.save(imgByteArr, format='PNG')
        imgByteArr = imgByteArr.getvalue()
        imgURL = save_to_azure_bytes(imgByteArr, str(slot_time)+".jpg")
        facesDetected = CF.face.detect(imgURL)
        for face in facesDetected:
            faceIds.append(face['faceId'])
            top = face['faceRectangle']['top']
            left = face['faceRectangle']['left']
            width = face['faceRectangle']['width']
            height = face['faceRectangle']['height']
            faceImg = j.crop((left, top, left+width, top+height))
            faceImg.save(os.path.join(FACE_DIR, face['faceId']+'.png'), 'PNG')
        faces[slot_time] = facesDetected
        current_time = slot
    similar_faces = CF.face.group(faceIds)

    data = {
        'hardcuts': filtered_slots,
        'faceIds': faceIds,
        'faceGroups': similar_faces,
        'faces': faces
    }

    with open(results, 'w+') as fhand:
        json.dump(data, fhand, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file')
    parser.add_argument('-m', '--mode')
    parser.add_argument('-r', '--results')

    args = parser.parse_args()
    MODE = args.mode
    get_face_ids(args.file, args.results)
