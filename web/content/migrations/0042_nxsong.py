# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-07-02 20:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0016_video_created_by'),
        ('content', '0041_auto_20180628_1921'),
    ]

    operations = [
        migrations.CreateModel(
            name='NxSong',
            fields=[
                ('song_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='content.Song')),
                ('content_id', models.CharField(blank=True, max_length=128, null=True)),
                ('is_processed', models.BooleanField(default=False)),
                ('video', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='video.Video')),
            ],
            options={
                'permissions': (('view_nxsong', 'Can view nx song'),),
            },
            bases=('content.song',),
        ),
    ]
