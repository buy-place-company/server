# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('statistic', '0002_auto_20150416_0514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statistic',
            name='counter',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='statistic',
            name='zone_id',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
    ]
