# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-07-26 19:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0029_auto_20190720_1805'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendorreportcommercial',
            name='commercial',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.VendorCommercial'),
        ),
        migrations.AlterField(
            model_name='vendorreportprogram',
            name='program',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.VendorProgram'),
        ),
        migrations.AlterField(
            model_name='vendorreportpromo',
            name='promo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.VendorPromo'),
        ),
    ]
