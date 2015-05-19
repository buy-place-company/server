# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0003_zone_parent_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zone',
            name='parent_id',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
    ]
