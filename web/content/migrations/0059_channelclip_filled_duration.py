# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-02-19 07:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0058_channel_channel_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='channelclip',
            name='filled_duration',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
