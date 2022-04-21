# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2021-06-28 13:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0103_auto_20210616_1943'),
    ]

    operations = [
        migrations.AddField(
            model_name='emotiontag',
            name='confidence',
            field=models.FloatField(blank=True, default=0.0, null=True),
        ),
        migrations.AddField(
            model_name='frametag',
            name='confidence',
            field=models.FloatField(blank=True, default=0.0, null=True),
        ),
    ]