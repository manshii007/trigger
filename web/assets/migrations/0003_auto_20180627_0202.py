# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-06-27 02:02
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0002_auto_20180627_0130'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ro',
            options={'ordering': ['-created_on'], 'permissions': (('view_ro', 'Can view ro'),)},
        ),
    ]
