# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-12-27 07:49
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0082_metadata_audio'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='metadata_audio',
            new_name='MetadataAudio',
        ),
    ]