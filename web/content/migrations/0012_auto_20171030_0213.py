# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-10-30 02:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0011_auto_20171022_0823'),
    ]

    operations = [
        migrations.AddField(
            model_name='politician',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='politician',
            name='modified_on',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
