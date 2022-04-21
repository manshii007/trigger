# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-11-06 13:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0004_ro_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='ro',
            name='process_eta',
            field=models.FloatField(default=0.0, null=True),
        ),
        migrations.AddField(
            model_name='ro',
            name='process_status',
            field=models.CharField(choices=[('CMP', 'Completed'), ('ERR', 'Error'), ('NPR', 'Not Processed'), ('PRO', 'Processing')], default='NPR', max_length=3, null=True),
        ),
    ]