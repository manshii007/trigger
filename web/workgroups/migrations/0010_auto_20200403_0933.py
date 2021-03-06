# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-03 09:33
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workgroups', '0009_workgroupmembership'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workgroupmembership',
            name='workgroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='workgroups.WorkGroup'),
        ),
        migrations.AlterUniqueTogether(
            name='workgroupmembership',
            unique_together=set([('user', 'workgroup')]),
        ),
    ]
