# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-07-21 20:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0068_auto_20190721_1955'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advertiser',
            name='advertiser_group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.AdvertiserGroup'),
        ),
        migrations.AlterField(
            model_name='brandcategory',
            name='brand_sector',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.BrandSector'),
        ),
        migrations.AlterField(
            model_name='brandname',
            name='brand_category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.BrandCategory'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='genre',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.ChannelGenre'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='language',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.ContentLanguage'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='network',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.ChannelNetwork'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='region',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.Region'),
        ),
        migrations.AlterField(
            model_name='commercial',
            name='advertiser',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.Advertiser'),
        ),
        migrations.AlterField(
            model_name='commercial',
            name='brand_name',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.BrandName'),
        ),
        migrations.AlterField(
            model_name='commercial',
            name='descriptor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.Descriptor'),
        ),
        migrations.AlterField(
            model_name='commercial',
            name='title',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.Title'),
        ),
        migrations.AlterField(
            model_name='program',
            name='channel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.Channel'),
        ),
        migrations.AlterField(
            model_name='program',
            name='language',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.ContentLanguage'),
        ),
        migrations.AlterField(
            model_name='program',
            name='prod_house',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.ProductionHouse'),
        ),
        migrations.AlterField(
            model_name='program',
            name='program_genre',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.ProgramGenre'),
        ),
        migrations.AlterField(
            model_name='program',
            name='title',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.Title'),
        ),
        migrations.AlterField(
            model_name='programgenre',
            name='program_theme',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.ProgramTheme'),
        ),
        migrations.AlterField(
            model_name='promo',
            name='advertiser',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.Advertiser'),
        ),
        migrations.AlterField(
            model_name='promo',
            name='brand_name',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.BrandName'),
        ),
        migrations.AlterField(
            model_name='promo',
            name='channel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='broadcasted_promo', to='tags.Channel'),
        ),
        migrations.AlterField(
            model_name='promo',
            name='descriptor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.Descriptor'),
        ),
        migrations.AlterField(
            model_name='promo',
            name='promo_channel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='self_promo', to='tags.Channel'),
        ),
        migrations.AlterField(
            model_name='promo',
            name='title',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.Title'),
        ),
    ]
