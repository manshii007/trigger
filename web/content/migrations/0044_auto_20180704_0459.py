# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-07-04 04:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0043_song_music_directors'),
    ]

    operations = [
        migrations.AddField(
            model_name='trivia',
            name='edit_request',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trivia',
            name='edit_status',
            field=models.CharField(blank=True, choices=[('RIV', 'Review'), ('CLN', 'Clean'), ('ACP', 'Accepted'), ('NCP', 'Not Accepted')], max_length=3, null=True),
        ),
    ]