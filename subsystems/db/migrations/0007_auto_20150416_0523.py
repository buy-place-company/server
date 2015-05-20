# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0006_auto_20150416_0521'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zone',
            name='parent_id',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
