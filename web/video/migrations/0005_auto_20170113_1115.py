# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-01-13 11:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0004_auto_20170113_0732'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='video',
            options={'permissions': (('view_video', 'Can view video'),)},
        ),
    ]
