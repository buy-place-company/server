# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0005_auto_20150416_0521'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='zone',
            name='ne_lat',
        ),
        migrations.RemoveField(
            model_name='zone',
            name='ne_lng',
        ),
        migrations.RemoveField(
            model_name='zone',
            name='sw_lat',
        ),
        migrations.RemoveField(
            model_name='zone',
            name='sw_lng',
        ),
    ]
