# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-11-08 08:12
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0075_auto_20191108_0756'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='channel',
            name='poster',
        ),
        migrations.RemoveField(
            model_name='channel',
            name='poster_ppoi',
        ),
    ]