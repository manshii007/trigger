# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-31 13:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0035_auto_20200127_1238'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoproxypath',
            name='nbm',
            field=models.TextField(blank=True, max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='videoproxypath',
            name='sourceproxy_upload_status',
            field=models.CharField(blank=True, choices=[('UPL', 'Uploading'), ('FAI', 'Uploading Failed'), ('NST', 'Uploading not Started'), ('UPD', 'Sucessfully Uploaded')], default='NST', max_length=3, null=True),
        ),
    ]
