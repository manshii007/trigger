# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-12-10 05:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0027_auto_20181209_1141'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='barctag',
            name='brand_sector',
        ),
        migrations.AlterField(
            model_name='barctag',
            name='advertiser',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='barctag',
            name='advertiser_group',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='barctag',
            name='brand_category',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='barctag',
            name='brand_title',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='barctag',
            name='descriptor',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='barctag',
            name='program_genre',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='barctag',
            name='program_theme',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
