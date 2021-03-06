# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-10-22 08:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0011_auto_20171022_0823'),
        ('frames', '0008_auto_20170515_0924'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonFrame',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('frame', models.OneToOneField(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='frames.Frames')),
                ('person', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.Person')),
            ],
        ),
    ]
