# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2021-06-18 05:16
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0068_video_picture'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='aws_face_json',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='video',
            name='aws_object_json',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
