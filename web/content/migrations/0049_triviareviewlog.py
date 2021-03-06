# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-07-19 08:04
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0048_triviaeditlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='TriviaReviewLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_approved_before', models.BooleanField()),
                ('is_approved_after', models.BooleanField()),
                ('edit_status_before', models.CharField(blank=True, choices=[('RIV', 'Review'), ('CLN', 'Clean'), ('ACP', 'Accepted'), ('NCP', 'Not Accepted'), ('CHK', 'Check')], default='CLN', max_length=3, null=True)),
                ('edit_status_after', models.CharField(blank=True, choices=[('RIV', 'Review'), ('CLN', 'Clean'), ('ACP', 'Accepted'), ('NCP', 'Not Accepted'), ('CHK', 'Check')], default='CLN', max_length=3, null=True)),
                ('timestamp', models.DateTimeField()),
                ('trivia', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.Trivia')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
