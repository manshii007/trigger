# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-11-19 09:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0078_auto_20191115_1237'),
    ]

    operations = [
        migrations.AddField(
            model_name='frametag',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='frametag',
            name='modified_on',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
