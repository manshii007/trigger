# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-07 04:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0011_auto_20190507_0426'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='supercommercial',
            unique_together=set([]),
        ),
        migrations.AlterUniqueTogether(
            name='superprogram',
            unique_together=set([]),
        ),
    ]
