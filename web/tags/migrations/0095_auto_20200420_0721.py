# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-20 07:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0094_auto_20200420_0718'),
    ]

    operations = [
        migrations.AddField(
            model_name='frametag',
            name='is_approved',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='keywordtag',
            name='is_approved',
            field=models.BooleanField(default=True),
        ),
    ]
