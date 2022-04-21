# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-07-21 07:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0062_auto_20190719_1528'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='abbr',
            field=models.CharField(max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='channel',
            name='code',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='channelgenre',
            name='code',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='channelnetwork',
            name='code',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='promocategory',
            name='code',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='region',
            name='code',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
