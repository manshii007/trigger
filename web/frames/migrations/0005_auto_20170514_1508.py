# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-05-14 15:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import utils.unique_filename
import uuid
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0007_framejob_tags'),
        ('contextual', '0006_auto_20170514_1508'),
        ('video', '0012_auto_20170505_0351'),
        ('frames', '0004_videoframes_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='PictureFrame',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('frame', models.OneToOneField(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='frames.Frames')),
            ],
        ),
        migrations.CreateModel(
            name='ProxyFrame',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', versatileimagefield.fields.VersatileImageField(null=True, upload_to=utils.unique_filename.unique_upload, verbose_name='Picture')),
                ('file_ppoi', versatileimagefield.fields.PPOIField(default='0.5x0.5', editable=False, max_length=20)),
                ('frame', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='frames.Frames')),
            ],
        ),
        migrations.CreateModel(
            name='VideoFrame',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('time', models.FloatField(default=0, null=True)),
                ('frame', models.OneToOneField(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='frames.Frames')),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='video.Video')),
            ],
        ),
        migrations.RemoveField(
            model_name='facerect',
            name='frame',
        ),
        migrations.RemoveField(
            model_name='videoframes',
            name='frames_ptr',
        ),
        migrations.RemoveField(
            model_name='videoframes',
            name='video',
        ),
        migrations.DeleteModel(
            name='FaceRect',
        ),
        migrations.DeleteModel(
            name='VideoFrames',
        ),
    ]
