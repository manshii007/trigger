# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-05-21 07:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0152_auto_20200520_1509'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movie',
            name='duration',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='makers',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='prod_year',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='production',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='role',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='type_movie',
        ),
    ]