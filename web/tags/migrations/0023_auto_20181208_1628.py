# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-12-08 16:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0022_barctag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='barctag',
            name='promo_sponsor_name',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
