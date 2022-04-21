# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-20 08:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0100_auto_20200120_0811'),
    ]

    operations = [
        migrations.AddField(
            model_name='segment',
            name='duration',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='segment',
            name='end_of_media',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='segment',
            name='start_of_media',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
