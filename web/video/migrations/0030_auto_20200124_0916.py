# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-24 09:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0029_auto_20200122_0947'),
    ]

    operations = [
        migrations.AddField(
            model_name='videoproxypath',
            name='metadata',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='videoproxypath',
            name='sourceproxy_upload_status',
            field=models.CharField(blank=True, choices=[('UPD', 'Sucessfully Uploaded'), ('FAI', 'Uploading Failed'), ('UPL', 'Uploading'), ('NST', 'Uploading not Started')], default='NST', max_length=3, null=True),
        ),
    ]
