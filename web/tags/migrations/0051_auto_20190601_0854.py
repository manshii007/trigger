# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-06-01 08:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0050_auto_20190313_1411'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advertiser',
            name='code',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='advertiser',
            name='name',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name='brandcategory',
            name='name',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name='brandname',
            name='name',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name='programgenre',
            name='code',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='programgenre',
            name='name',
            field=models.CharField(max_length=128),
        ),
    ]
