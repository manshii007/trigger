# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-07-11 20:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0046_song_actors'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trivia',
            name='edit_status',
            field=models.CharField(blank=True, choices=[('RIV', 'Review'), ('CLN', 'Clean'), ('ACP', 'Accepted'), ('NCP', 'Not Accepted'), ('CHK', 'Check')], default='CLN', max_length=3, null=True),
        ),
    ]