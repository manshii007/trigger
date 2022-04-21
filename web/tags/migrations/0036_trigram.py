from __future__ import unicode_literals

from django.db import migrations
from django.contrib.postgres import operations


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0035_auto_20181228_0340'),
    ]

    operations = [
        operations.TrigramExtension(),
    ]