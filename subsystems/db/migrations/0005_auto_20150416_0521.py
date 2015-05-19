# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0004_auto_20150416_0517'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='zone',
            name='timestamp',
        ),
        migrations.AlterField(
            model_name='zone',
            name='list_id',
            field=models.CharField(max_length=255, unique=True),
            preserve_default=True,
        ),
    ]
