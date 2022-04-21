# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-05-20 09:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0149_auto_20200519_0634'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='songasset',
            name='duration',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='lyrics',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='music_directors',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='prod_year',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='production',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='role',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='song_id',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='type_song',
        ),
        migrations.AlterField(
            model_name='songasset',
            name='original_remake',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='songasset',
            name='version',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
