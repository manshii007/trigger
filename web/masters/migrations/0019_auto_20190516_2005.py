# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-16 20:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0018_vendormastercomparison_step'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendorcommercial',
            name='descriptor',
            field=models.CharField(db_index=True, max_length=128),
        ),
        migrations.AlterField(
            model_name='vendorcommercial',
            name='title',
            field=models.CharField(db_index=True, max_length=128),
        ),
    ]
