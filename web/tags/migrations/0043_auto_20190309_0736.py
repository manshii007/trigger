# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-03-09 07:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0042_auto_20190307_0813'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commercial',
            name='advertiser',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.Advertiser'),
        ),
        migrations.AlterField(
            model_name='commercial',
            name='descriptor',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.Descriptor'),
        ),
        migrations.AlterField(
            model_name='program',
            name='language',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.ContentLanguage'),
        ),
        migrations.AlterField(
            model_name='program',
            name='prod_house',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.ProductionHouse'),
        ),
        migrations.AlterField(
            model_name='program',
            name='program_genre',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.ProgramGenre'),
        ),
        migrations.AlterField(
            model_name='promo',
            name='advertiser',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.Advertiser'),
        ),
        migrations.AlterField(
            model_name='promo',
            name='descriptor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.Descriptor'),
        ),
    ]
