# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-01-15 10:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workgroups', '0002_workgroup_library'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workgroup',
            name='name',
            field=models.CharField(max_length=128, null=True, unique=True, verbose_name='Workgroup Name'),
        ),
    ]