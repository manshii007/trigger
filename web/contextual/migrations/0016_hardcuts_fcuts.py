# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-06 13:27
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contextual', '0015_auto_20191217_1159'),
    ]

    operations = [
        migrations.AddField(
            model_name='hardcuts',
            name='fcuts',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), size=None), default=[[]], size=None),
            preserve_default=False,
        ),
    ]
