# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-03-13 13:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0048_auto_20190312_0351'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advertiser',
            name='code',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='advertisergroup',
            name='code',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='brandcategory',
            name='code',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='brandname',
            name='code',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='brandsector',
            name='code',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
