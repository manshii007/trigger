# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-01-19 18:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0006_video_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='frame_rate',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='video',
            name='height',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='video',
            name='width',
            field=models.IntegerField(null=True),
        ),
    ]
