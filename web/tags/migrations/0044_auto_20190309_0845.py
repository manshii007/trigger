# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-03-09 08:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0043_auto_20190309_0736'),
    ]

    operations = [
        migrations.AlterField(
            model_name='descriptor',
            name='code',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='title',
            name='code',
            field=models.IntegerField(),
        ),
    ]
