# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-06-04 07:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0035_auto_20180508_0914'),
    ]

    operations = [
        migrations.AddField(
            model_name='trivia',
            name='original_description',
            field=models.TextField(blank=True, null=True),
        ),
    ]