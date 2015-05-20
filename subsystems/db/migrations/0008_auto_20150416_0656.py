# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0007_auto_20150416_0523'),
    ]

    operations = [
        migrations.AddField(
            model_name='zone',
            name='ne_lat',
            field=models.FloatField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='zone',
            name='ne_lng',
            field=models.FloatField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='zone',
            name='sw_lat',
            field=models.FloatField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='zone',
            name='sw_lng',
            field=models.FloatField(default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='zone',
            name='list_id',
            field=models.CharField(max_length=255),
            preserve_default=True,
        ),
    ]
