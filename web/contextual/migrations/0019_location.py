# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-06-14 17:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0099_auto_20200525_1127'),
        ('contextual', '0018_auto_20200518_1059'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('locations', models.ManyToManyField(to='tags.GenericTag')),
                ('manual_tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tags.ManualTag')),
            ],
        ),
    ]