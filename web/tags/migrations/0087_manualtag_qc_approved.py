# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-21 12:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0086_auto_20200108_0812'),
    ]

    operations = [
        migrations.AddField(
            model_name='manualtag',
            name='qc_approved',
            field=models.BooleanField(default=True),
        ),
    ]
