# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-01-12 17:07
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0004_delete_frametagcategory'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='frametag',
            options={'permissions': (('view_frametag', 'Can view frame tags'),)},
        ),
        migrations.AlterModelOptions(
            name='tag',
            options={'permissions': (('view_tag', 'Can view tag'),)},
        ),
        migrations.AlterModelOptions(
            name='tagcategory',
            options={'permissions': (('view_tagcategory', 'Can view tag category'),)},
        ),
        migrations.AlterModelOptions(
            name='taggeditem',
            options={'permissions': (('view_taggeditem', 'Can view tagged item'),)},
        ),
    ]
