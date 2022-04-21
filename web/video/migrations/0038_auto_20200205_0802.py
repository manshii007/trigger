# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-02-05 08:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0037_auto_20200131_1333'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoproxypath',
            name='sourceproxy_upload_status',
            field=models.CharField(blank=True, choices=[('NST', 'Uploading not Started'), ('UPL', 'Uploading'), ('UPD', 'Sucessfully Uploaded'), ('FAI', 'Uploading Failed')], default='NST', max_length=3, null=True),
        ),
    ]
