# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-03 09:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workgroups', '0010_auto_20200403_0933'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workgroupmembership',
            name='role',
        ),
        migrations.AddField(
            model_name='workgroupmembership',
            name='role',
            field=models.ManyToManyField(to='workgroups.Role'),
        ),
    ]
