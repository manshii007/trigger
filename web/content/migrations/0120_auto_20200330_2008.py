# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-03-30 20:08
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0119_auto_20200330_1251'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workflowstep',
            name='allowed_status',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('NSD', 'Not Started'), ('REV', 'Review'), ('APR', 'Approve'), ('APE', 'Approve with Edits'), ('REJ', 'Reject'), ('CMP', 'Completed'), ('FAI', 'Failed'), ('PAS', 'Pass')], max_length=100), blank=True, null=True, size=None),
        ),
    ]
