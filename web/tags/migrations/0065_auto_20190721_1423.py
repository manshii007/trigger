# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-07-21 14:23
from __future__ import unicode_literals

from django.db import migrations, models
import tags.models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0064_auto_20190721_1419'),
    ]

    operations = [
        migrations.AlterField(
            model_name='promocategory',
            name='code',
            field=models.IntegerField(blank=True, default=tags.models.random_code),
        ),
    ]