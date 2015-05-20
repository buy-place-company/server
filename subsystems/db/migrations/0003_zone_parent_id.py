# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0002_zone'),
    ]

    operations = [
        migrations.AddField(
            model_name='zone',
            name='parent_id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
