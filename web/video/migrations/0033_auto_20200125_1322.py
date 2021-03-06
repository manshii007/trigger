# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-25 13:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0032_auto_20200125_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoproxypath',
            name='sourceproxy_upload_status',
            field=models.CharField(blank=True, choices=[('FAI', 'Uploading Failed'), ('UPL', 'Uploading'), ('UPD', 'Sucessfully Uploaded'), ('NST', 'Uploading not Started')], default='NST', max_length=3, null=True),
        ),
    ]
