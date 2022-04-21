# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-20 07:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0095_auto_20200118_1246'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sequence',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, max_length=256, null=True, verbose_name='Title')),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'permissions': (('view_sequence', 'Can view sequence'),),
            },
        ),
        migrations.AlterField(
            model_name='segment',
            name='version',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='content.Sequence'),
        ),
    ]