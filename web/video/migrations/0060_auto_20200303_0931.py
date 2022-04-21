# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-03-03 09:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0059_auto_20200303_0608'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoproxypath',
            name='sourceproxy_upload_status',
            field=models.CharField(blank=True, choices=[('FAI', 'Uploading Failed'), ('UPD', 'Sucessfully Uploaded'), ('NST', 'Uploading not Started'), ('UPL', 'Uploading')], default='NST', max_length=3, null=True),
        ),
    ]