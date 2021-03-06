# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-21 09:18
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('jobs', '0012_subtitlesyncjob_srt_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScriptProcessJob',
            fields=[
                ('job_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='jobs.Job')),
                ('script_file', models.URLField()),
                ('txt_file', models.URLField(blank=True, null=True)),
                ('eta', models.FloatField(blank=True, default=0, null=True)),
                ('percent_complete', models.IntegerField(blank=True, default=0, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='script_process_jobs_given', to=settings.AUTH_USER_MODEL)),
            ],
            bases=('jobs.job',),
        ),
    ]
