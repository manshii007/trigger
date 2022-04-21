# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-25 14:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0096_auto_20200423_1618'),
        ('content', '0137_auto_20200425_1403'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assetversion',
            name='version_number',
        ),
        migrations.AddField(
            model_name='assetversion',
            name='audio_languages',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_audio_tracks', to='tags.ContentLanguage'),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='end_credit_end_time',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='end_credit_start_time',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='subtitle_languages',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_subtitle_tracks', to='tags.ContentLanguage'),
        ),
    ]
