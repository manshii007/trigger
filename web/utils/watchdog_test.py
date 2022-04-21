import time
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver as Observer
import logging, os
import json
import boto3
import http, urllib
import os
import datetime
SUBPROCESS_HAS_TIMEOUT = True

s3 = boto3.client('s3')

# api_url = "172.25.28.136"
api_url = "3.6.111.186"

asset_mapping = {
        'movies': 'movies',
        'rushes': 'rushes',
        'promos': 'promo',
        'commercials': 'commercialasset',
        'songs': 'songasset'
    }

# bucket_name = "trigger-demo-media"

def get_token():
    conn = http.client.HTTPConnection(api_url)

    payload = "------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"username\"\r\n\r\ntest_user\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"password\"\r\n\r\ntest123\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--"

    headers = {
        'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        'cache-control': "no-cache",
        'postman-token': "c286a88b-d3f6-b8eb-28d8-e9214b5adab7"
        }

    conn.request("POST", "/auth/login/", payload, headers)

    res = conn.getresponse()
    data = res.read()
    token = json.loads(data.decode('utf-8'))

    print(token)
    return token

def get_channel(token, channel_name):
    conn = http.client.HTTPConnection(api_url)

    headers = {
        'authorization': "Token {}".format(token['auth_token']),
        'content-type': "application/x-www-form-urlencoded",
    }

    # quoted channel_name to accomodate invalid characters
    conn.request("GET", "/api/v1/channels/?channel_name={}".format(urllib.parse.quote(channel_name)), body=None, headers=headers)

    res = conn.getresponse()
    data = res.read()
    channel_result = json.loads(data.decode('utf-8'))
    channel_list = channel_result['results']
    if(len(channel_list) != 0):
        return channel_list[0]
    return None

def create_asset(token, title, channel_id, asset_type, ingested_on):
    conn = http.client.HTTPConnection(api_url)

    payload = None
    if ingested_on is not None:
        payload = {
            "poster": "",
            "title": "{}".format(title),
            "language": "",
            "content_subject": "",
            "content_synopsis": "",
            "channel": channel_id,
            "ingested_on": ingested_on
        }
    else:
        payload = {
            "poster": "",
            "title": "{}".format(title),
            "language": "",
            "content_subject": "",
            "content_synopsis": "",
            "channel": channel_id,
            "ingested_on": str(datetime.datetime.today().date())
        }
    queries = urllib.parse.urlencode(payload)
    headers = {
        'authorization': "Token {}".format(token['auth_token']),
        'content-type': "application/x-www-form-urlencoded",
    }

    conn.request("POST", "/api/v1/{}/".format(asset_mapping[asset_type]), queries, headers)

    res = conn.getresponse()
    data = res.read()
    asset_response = json.loads(data.decode('utf-8'))
    return asset_response

def create_video(token, title, url, videoproxy_path_id):
    conn = http.client.HTTPConnection(api_url)

    payload = None
    if videoproxy_path_id is not None:
        payload = {
            "title": "{}".format(title),
            "file": url,
            "metadata": videoproxy_path_id
        }
    else:
        payload = {
            "title": "{}".format(title),
            "file": url
        }
    queries = urllib.parse.urlencode(payload)
    headers = {
        'authorization': "Token {}".format(token['auth_token']),
        'content-type': "application/x-www-form-urlencoded",
    }

    conn.request("POST", "/api/v1/videos/", queries, headers)

    res = conn.getresponse()
    data = res.read()
    print(data)
    video_resp = json.loads(data.decode('utf-8'))
    return video_resp

def get_content_type(token, asset_type):
    conn = http.client.HTTPConnection(api_url)

    headers = {
        'authorization': "Token {}".format(token['auth_token']),
        'content-type': "application/x-www-form-urlencoded",
    }

    model_type = asset_mapping[asset_type]
    if asset_mapping[asset_type] == "movies":
        model_type = "movie"

    conn.request("GET", "/api/v1/contenttype/?search={}&app_label={}".format(model_type, "content"), body=None, headers=headers)

    res = conn.getresponse()
    data = res.read()
    content_types = json.loads(data.decode('utf-8'))
    content_type_list = content_types['results']
    if(len(content_type_list) != 0):
        return content_type_list[0]
    return None


def create_asset_version(token, title, asset_id, video_id, content_type, file_name):
    conn = http.client.HTTPConnection(api_url)

    payload = {
        "title": "{}".format(title),
        "version_number": "",
        "object_id": asset_id,
        "content_type": content_type,
        "notes": file_name,
        "is_active": True
    }
    queries = urllib.parse.urlencode(payload)
    headers = {
        'authorization': "Token {}".format(token['auth_token']),
        'content-type': "application/x-www-form-urlencoded",
    }

    conn.request("POST", "/api/v1/assetversion/", queries, headers)

    res = conn.getresponse()
    data = res.read()
    asset_version_response = json.loads(data.decode('utf-8'))
    return asset_version_response


class Watcher:
    DIRECTORY_TO_WATCH = "/data/"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(PatternMatchingEventHandler):
    def __init__(self):
        super(Handler, self).__init__(ignore_patterns=["*.fctmp*"])

    @staticmethod
    def on_any_event(event):
        print(event.src_path, event.event_type)
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            logging.error("Received created event - %s." % event.src_path)

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            # this is called when f.close() is called
            logging.error("Received modified event - %s." % event.src_path)
            file_name = os.path.basename(event.src_path)
            # 9XM, 9X, 9XO, 9X Jalwa, 9X Jhakaas, 9X Tashan, SpotboyE
            file_extensions = set(["mp4", "mxF", "mov", "MTS", "mts", "mxf"])
            token = get_token()

            videoproxy_path_id = None
            ingested_on = None

            print(videoproxy_path_id)

            channel = get_channel(token, 'Viacom')
            channel_id = None

            if(channel):
                channel_id = channel['id']

            # file_name = tmp.mp4
            print("---------{}-----------{}----------------".format("ChannelId", channel_id))
            asset = create_asset(token, file_name.split(".")[0], channel_id, 'rushes', ingested_on)
            asset_id = asset['id']
            # video = create_video(token, file_name, 'http://trigger-d.com', videoproxy_path_id)
            # print(video)
            video = None
            video_id = None
            if(video):
                video_id = video['id']
            print("---------{}-----------{}----------------".format("VideoId", video_id))
            content_type = get_content_type(token, 'rushes')
            content_type_id = None
            if(content_type):
                content_type_id = content_type['id']
            print("---------{}-----------{}----------------".format("ContentTypeId", content_type_id))

            asset_version  = create_asset_version(token, file_name.split(".")[0], asset_id, video_id, content_type_id, event.src_path)
            print("---------{}-----------{}----------------".format("AssetVersionId", asset_version['id']))


if __name__ == '__main__':
    print("Starting Watcher")
    w = Watcher()
    w.run()
