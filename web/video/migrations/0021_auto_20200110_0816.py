# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-10 08:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0020_auto_20200109_0904'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='videoproxypath',
            name='intermediate',
        ),
        migrations.RemoveField(
            model_name='videoproxypath',
            name='master',
        ),
    ]
