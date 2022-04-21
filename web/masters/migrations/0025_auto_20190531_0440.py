# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-31 04:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0024_auto_20190522_1137'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendorcommercial',
            name='similars',
            field=models.ManyToManyField(blank=True, related_name='_vendorcommercial_similars_+', to='masters.VendorCommercial'),
        ),
        migrations.AddField(
            model_name='vendorprogram',
            name='similars',
            field=models.ManyToManyField(blank=True, related_name='_vendorprogram_similars_+', to='masters.VendorProgram'),
        ),
        migrations.AddField(
            model_name='vendorpromo',
            name='similars',
            field=models.ManyToManyField(blank=True, related_name='_vendorpromo_similars_+', to='masters.VendorPromo'),
        ),
    ]