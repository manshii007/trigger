# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-03-03 07:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0017_auto_20180303_0700'),
    ]

    operations = [
        migrations.AlterField(
            model_name='series',
            name='genre',
            field=models.ManyToManyField(blank=True, null=True, to='content.Genre'),
        ),
        migrations.AlterField(
            model_name='series',
            name='number_of_episodes',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='series',
            name='year_of_release',
            field=models.DateField(blank=True, null=True),
        ),
    ]
