# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-02-19 11:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0112_remove_assetversion_video_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoprocessingstatus',
            name='video',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='video.Video'),
        ),
    ]
