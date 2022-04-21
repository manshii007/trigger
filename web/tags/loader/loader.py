from .load_brandmaster import load as load_brand
from .load_programmaster import load as load_program
from .load_promomaster import load as load_promo
from .load_channelmaster import load as load_channel
from .load_contentlanguagemaster import load as load_contentlanguage
from .load_genremaster import load as load_genre
from .load_promocategorymaster import load as load_promocategory
import requests
import argparse
import shutil
import os
from video.tasks import check_or_create_file, silentremove
import subprocess


def clean_file(file, url):
    tmp_file = os.path.join("/tmp", file.split("/")[-1])
    check_or_create_file(tmp_file)

    if url:
        with requests.get(file, stream=True) as r:
            with open(tmp_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    else:
        subprocess.run(["cp", file, tmp_file])

    tmp_tmp = tmp_file + ".tmp"
    subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, tmp_file])

    subprocess.run(["mv", tmp_tmp, tmp_file])
    silentremove(tmp_tmp)
    return tmp_file


def load_base(file, url=True):
    tmp_file = clean_file(file, url)
    load_brand(tmp_file)
    silentremove(tmp_file)


def load_channelmaster(file, url=True):
    tmp_file = clean_file(file, url)
    load_channel(tmp_file)
    silentremove(tmp_file)


def load_promocategorymaster(file, url=True):
    tmp_file = clean_file(file, url)
    load_promocategory(tmp_file)
    silentremove(tmp_file)


def load_genremaster(file, url=True):
    tmp_file = clean_file(file, url)
    load_genre(tmp_file)
    silentremove(tmp_file)


def load_contentlanguagemaster(file, url=True):
    tmp_file = clean_file(file, url)
    load_contentlanguage(tmp_file)
    silentremove(tmp_file)


def load_promomaster(file, url=True):
    tmp_file = clean_file(file, url)
    load_promo(tmp_file)
    silentremove(tmp_file)


def load_prgmaster(file, url=True):
    tmp_file = clean_file(file, url)
    load_program(tmp_file)
    silentremove(tmp_file)