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


def load_base(file, date, vendor, url=True):
    tmp_file = os.path.join("/tmp/{}/".format(vendor), file.split("/")[-1])
    check_or_create_file(tmp_file)

    if url:
        with requests.get(file, stream=True) as r:
            with open(tmp_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    else:
        subprocess.run(["cp", file, tmp_file])

    tmp_tmp = tmp_file+".tmp"
    subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, tmp_file])

    subprocess.run(["mv", tmp_tmp, tmp_file])
    load_brand(tmp_file, vendor)
    silentremove(tmp_file)
    silentremove(tmp_tmp)


def load_channelmaster(file, date, vendor, url=True):
    tmp_file = os.path.join("/tmp/{}/".format(vendor), file.split("/")[-1])
    check_or_create_file(tmp_file)

    if url:
        with requests.get(file, stream=True) as r:
            with open(tmp_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    else:
        subprocess.run(["cp", file, tmp_file])

    tmp_tmp = tmp_file+".tmp"
    subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, tmp_file])

    subprocess.run(["mv", tmp_tmp, tmp_file])
    load_channel(tmp_file, vendor)
    silentremove(tmp_file)
    silentremove(tmp_tmp)


def load_promocategorymaster(file, date, vendor, url=True):
    tmp_file = os.path.join("/tmp/{}/".format(vendor), file.split("/")[-1])
    check_or_create_file(tmp_file)

    if url:
        with requests.get(file, stream=True) as r:
            with open(tmp_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    else:
        subprocess.run(["cp", file, tmp_file])

    tmp_tmp = tmp_file+".tmp"
    subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, tmp_file])

    subprocess.run(["mv", tmp_tmp, tmp_file])
    load_promocategory(tmp_file, vendor)
    silentremove(tmp_file)
    silentremove(tmp_tmp)


def load_genremaster(file, date, vendor, url=True):
    tmp_file = os.path.join("/tmp/{}/".format(vendor), file.split("/")[-1])
    check_or_create_file(tmp_file)

    if url:
        with requests.get(file, stream=True) as r:
            with open(tmp_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    else:
        subprocess.run(["cp", file, tmp_file])

    tmp_tmp = tmp_file+".tmp"
    subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, tmp_file])

    subprocess.run(["mv", tmp_tmp, tmp_file])
    load_genre(tmp_file, vendor)
    silentremove(tmp_file)
    silentremove(tmp_tmp)


def load_contentlanguagemaster(file, date, vendor, url=True):
    tmp_file = os.path.join("/tmp/{}/".format(vendor), file.split("/")[-1])
    check_or_create_file(tmp_file)

    if url:
        with requests.get(file, stream=True) as r:
            with open(tmp_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    else:
        subprocess.run(["cp", file, tmp_file])

    tmp_tmp = tmp_file+".tmp"
    subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, tmp_file])

    subprocess.run(["mv", tmp_tmp, tmp_file])
    load_contentlanguage(tmp_file, vendor)
    silentremove(tmp_file)
    silentremove(tmp_tmp)


def load_promomaster(file, date, vendor, url=True):
    tmp_file = os.path.join("/tmp/{}/".format(vendor), file.split("/")[-1])
    check_or_create_file(tmp_file)

    if url:
        with requests.get(file, stream=True) as r:
            with open(tmp_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    else:
        subprocess.run(["cp", file, tmp_file])
    tmp_tmp = tmp_file+".tmp"
    subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, tmp_file])

    subprocess.run(["mv", tmp_tmp, tmp_file])
    load_promo(tmp_file, vendor)
    silentremove(tmp_file)
    silentremove(tmp_tmp)


def load_prgmaster(file, date, vendor, loc=0, url=True):
    tmp_file = os.path.join("/tmp/{}/".format(vendor), file.split("/")[-1])
    check_or_create_file(tmp_file)

    if url:
        with requests.get(file, stream=True) as r:
            with open(tmp_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    else:
        subprocess.run(["cp", file, tmp_file])

    tmp_tmp = tmp_file+".tmp"
    subprocess.run(["iconv", "-f", "utf-8", "-t", "utf-8", "-c", "-o", tmp_tmp, tmp_file])

    subprocess.run(["mv", tmp_tmp, tmp_file])
    load_program(tmp_file, vendor, loc)
    silentremove(tmp_file)
    silentremove(tmp_tmp)