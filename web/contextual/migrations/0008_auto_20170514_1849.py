# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-05-14 18:49
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('frames', '0006_auto_20170514_1849'),
        ('contextual', '0007_picturegroup_frames'),
    ]

    operations = [
        migrations.CreateModel(
            name='FrameGroup',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('face_groups', models.ManyToManyField(to='contextual.FaceGroup')),
                ('frames', models.ManyToManyField(to='frames.Frames')),
            ],
        ),
        migrations.AlterModelOptions(
            name='hardcuts',
            options={'verbose_name_plural': 'Hard cuts'},
        ),
    ]
