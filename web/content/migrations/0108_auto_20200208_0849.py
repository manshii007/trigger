# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-02-08 08:49
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0107_auto_20200205_0802'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowinstance',
            name='work_flow_step_status',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='workflowstep',
            name='allowed_status',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('NS', 'Not Started'), ('APR', 'Approve'), ('REJ', 'Reject'), ('RJE', 'Reject with Edits'), ('PS', 'Pass'), ('OK', 'Ok')], max_length=100), blank=True, null=True, size=None),
        ),
    ]
