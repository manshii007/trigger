# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-05-25 12:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0158_auto_20200525_1201'),
    ]

    operations = [
        migrations.AddField(
            model_name='commercialasset',
            name='channel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.Channel'),
        ),
    ]