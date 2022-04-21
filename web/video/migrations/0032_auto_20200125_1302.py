# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-25 13:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0031_auto_20200125_1230'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoproxypath',
            name='sourceproxy_upload_status',
            field=models.CharField(blank=True, choices=[('NST', 'Uploading not Started'), ('UPD', 'Sucessfully Uploaded'), ('UPL', 'Uploading'), ('FAI', 'Uploading Failed')], default='NST', max_length=3, null=True),
        ),
    ]