# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-05-15 09:24
from __future__ import unicode_literals

from django.db import migrations
import utils.unique_filename
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('frames', '0007_auto_20170515_0809'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proxyframe',
            name='file',
            field=versatileimagefield.fields.VersatileImageField(null=True, upload_to=utils.unique_filename.unique_upload, verbose_name='Picture'),
        ),
    ]
