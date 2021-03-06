# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-15 12:15
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0122_auto_20200415_0727'),
    ]

    operations = [
        migrations.AddField(
            model_name='assetversion',
            name='material_id',
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='actors',
            field=models.ManyToManyField(blank=True, related_name='movie_actors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='movie',
            name='aka_title',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='movie',
            name='barcode',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='certification',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='classification',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='country_of_origin',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='added_movie', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='movie',
            name='duration',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='external_ref_number',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='keywords',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='makers',
            field=models.ManyToManyField(blank=True, related_name='movie_makers', to='content.Person'),
        ),
        migrations.AddField(
            model_name='movie',
            name='movie_id',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='prod_year',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='production',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='production_house',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='production_number',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='role',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='short_synopsis',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='slot_duration',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='tx_id',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='tx_run_time',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='promo',
            name='aka_title',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='promo',
            name='certification',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='promo',
            name='country_of_origin',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='promo',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='added_promo', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='promo',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='workflowstage',
            name='work_flow',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='work_flow_stage', to='content.WorkFlow'),
        ),
    ]
