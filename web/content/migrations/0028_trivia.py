# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-03-12 16:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0027_person_partner_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trivia',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('trivia', models.TextField()),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='content.Movie')),
                ('persons', models.ManyToManyField(to='content.Person')),
            ],
            options={
                'permissions': (('view_trivia', 'Can view trivia'),),
            },
        ),
    ]
