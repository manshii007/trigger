# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-23 16:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0134_auto_20200423_1604'),
    ]

    operations = [
        migrations.AddField(
            model_name='assetversion',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
