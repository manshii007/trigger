# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-06-23 11:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0060_song_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='year',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
