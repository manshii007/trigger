# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-08-03 05:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0016_auto_20180524_1052'),
    ]

    operations = [
        migrations.AddField(
            model_name='frametag',
            name='words',
            field=models.TextField(null=True),
        ),
    ]