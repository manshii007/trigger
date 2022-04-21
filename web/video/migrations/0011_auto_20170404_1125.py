# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-04-04 11:25
from __future__ import unicode_literals

from django.db import migrations
import utils.unique_filename
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0010_auto_20170404_0601'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='poster',
            field=versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to=utils.unique_filename.unique_upload, verbose_name='Poster'),
        ),
    ]