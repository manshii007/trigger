# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-16 07:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0023_auto_20200114_1241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoproxypath',
            name='sourceproxy_processing_status',
            field=models.CharField(blank=True, choices=[('NPR', 'Not Processed'), ('QUE', 'Queued'), ('PRD', 'Processed'), ('PRO', 'Processing'), ('FAI', 'Failed')], default='NPR', max_length=3, null=True),
        ),
    ]
