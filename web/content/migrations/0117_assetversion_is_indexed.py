# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-03-25 08:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0116_auto_20200317_1059'),
    ]

    operations = [
        migrations.AddField(
            model_name='assetversion',
            name='is_indexed',
            field=models.BooleanField(default=False),
        ),
    ]
