# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-03-12 08:28
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0025_auto_20180312_0828'),
        ('jobs', '0016_reviewtranslationjob'),
    ]

    operations = [
        migrations.CreateModel(
            name='EpisodeTranslationJob',
            fields=[
                ('job_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='jobs.Job')),
                ('source_subtitle', models.URLField(blank=True, null=True)),
                ('target_subtitle', models.URLField(blank=True, null=True)),
                ('target_language', models.CharField(choices=[('FR', 'French'), ('SP', 'Spanish'), ('EN', 'English'), ('HI', 'Hindi')], default='EN', max_length=2)),
                ('assigned_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='episode_translation_job_assigned', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='episode_translation_job_given', to=settings.AUTH_USER_MODEL)),
                ('episode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='content.Episode')),
                ('episode_segment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.EpisodeSegment')),
            ],
            options={
                'permissions': (('view_episodetranslationjob', 'Can view episode translation job'),),
            },
            bases=('jobs.job',),
        ),
        migrations.CreateModel(
            name='MovieTranslationJob',
            fields=[
                ('job_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='jobs.Job')),
                ('source_subtitle', models.URLField(blank=True, null=True)),
                ('target_subtitle', models.URLField(blank=True, null=True)),
                ('target_language', models.CharField(choices=[('FR', 'French'), ('SP', 'Spanish'), ('EN', 'English'), ('HI', 'Hindi')], default='EN', max_length=2)),
                ('assigned_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movie_translation_job_assigned', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movie_translation_job_given', to=settings.AUTH_USER_MODEL)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='content.Movie')),
                ('movie_segment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.MovieSegment')),
            ],
            options={
                'permissions': (('view_movietranslationjob', 'Can view movie translation job'),),
            },
            bases=('jobs.job',),
        ),
        migrations.AlterField(
            model_name='job',
            name='job_status',
            field=models.CharField(choices=[('APR', 'Approved'), ('REJ', 'Rejected'), ('PRO', 'Processing'), ('NPR', 'Not Processed'), ('EDT', 'Edit Required'), ('ASG', 'Assigned'), ('PRD', 'Processed'), ('WIP', 'Work In Progress'), ('REV', 'Review'), ('QAP', 'Quality Assurance')], default='NPR', max_length=3),
        ),
    ]
