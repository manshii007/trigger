# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-10-31 06:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0054_auto_20181028_1410'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='channel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.Channel'),
        ),
    ]
