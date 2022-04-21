# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-12-26 19:38
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0013_audio_subtitle_transcription'),
        ('content', '0014_politician_created_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='Credit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('credit', django.contrib.postgres.fields.jsonb.JSONField()),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='video.Video')),
            ],
            options={
                'permissions': (('view_credit', 'Can view credit'),),
            },
        ),
    ]