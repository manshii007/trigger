# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-03-07 08:13
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0041_fingerprint'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fingerprint',
            name='frequencies',
        ),
        migrations.RemoveField(
            model_name='fingerprint',
            name='time',
        ),
        migrations.AddField(
            model_name='fingerprint',
            name='fprint',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
    ]
