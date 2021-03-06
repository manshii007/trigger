# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-11-23 15:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0012_auto_20171030_0213'),
    ]

    operations = [
        migrations.CreateModel(
            name='TVAnchor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('books', models.TextField(blank=True, max_length=256, null=True)),
                ('organizations', models.TextField(blank=True, max_length=256, null=True)),
                ('notable_credits', models.TextField(blank=True, max_length=256, null=True)),
                ('awards', models.TextField(blank=True, max_length=256, null=True)),
                ('person', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='content.Person')),
            ],
            options={
                'permissions': (('view_tvanchor', 'Can view tvanchor'),),
            },
        ),
    ]
