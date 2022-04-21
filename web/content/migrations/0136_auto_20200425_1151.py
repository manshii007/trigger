# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-25 11:51
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0135_assetversion_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='workflow',
            options={'permissions': (('view_workflow', 'Can view work flow'),)},
        ),
        migrations.AlterModelOptions(
            name='workflowstep',
            options={'permissions': (('view_workflowstep', 'Can view work flow step'),)},
        ),
    ]