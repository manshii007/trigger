# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-02-18 12:02
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0111_assetversion_video_metadata'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assetversion',
            name='video_metadata',
        ),
    ]