# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-12-08 16:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0023_auto_20181208_1628'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='barctag',
            name='words',
        ),
    ]
