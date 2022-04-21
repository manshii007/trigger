# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-05-25 08:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0154_remove_songasset_makers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movie',
            name='cast',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='characters',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='content_synopsis',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='movie_id',
        ),
        migrations.AddField(
            model_name='commercialasset',
            name='ingested_on',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='ingested_on',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='ingested_on',
            field=models.DateField(blank=True, null=True),
        ),
    ]