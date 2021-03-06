# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-03-03 10:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0013_audio_subtitle_transcription'),
    ]

    operations = [
        migrations.CreateModel(
            name='VideoSubtitle',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('title', models.CharField(max_length=128)),
                ('subtitle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='video.Subtitle')),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='video.Video')),
            ],
            options={
                'permissions': (('view_videosubtitle', 'Can view video subtitle'),),
            },
        ),
    ]
