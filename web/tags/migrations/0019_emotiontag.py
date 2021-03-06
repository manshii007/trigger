# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-08-09 06:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0016_video_created_by'),
        ('tags', '0018_auto_20180807_1057'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmotionTag',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('frame_in', models.PositiveIntegerField()),
                ('frame_out', models.PositiveIntegerField()),
                ('emotion_quo', models.CharField(blank=True, max_length=64, null=True)),
                ('comment', models.TextField(null=True)),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='video.Video')),
            ],
            options={
                'permissions': (('view_emotiontag', 'Can view emotion tags'),),
            },
        ),
    ]
