# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-01-01 05:04
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Library',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('videos', models.ManyToManyField(to='video.Video')),
            ],
        ),
    ]
