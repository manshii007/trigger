# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-02-18 09:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0045_auto_20200218_0948'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoproxypath',
            name='sourceproxy_upload_status',
            field=models.CharField(blank=True, choices=[('NST', 'Uploading not Started'), ('UPL', 'Uploading'), ('FAI', 'Uploading Failed'), ('UPD', 'Sucessfully Uploaded')], default='NST', max_length=3, null=True),
        ),
    ]
