# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('statistic', '0003_auto_20150416_0517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statistic',
            name='zone_id',
            field=models.IntegerField(blank=True, null=True),
            preserve_default=True,
        ),
    ]
