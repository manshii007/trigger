# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-10-01 09:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0067_collection'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='user',
        ),
    ]