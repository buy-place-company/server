# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Zone',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('list_id', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField()),
                ('sw_lat', models.FloatField()),
                ('sw_lng', models.FloatField()),
                ('ne_lat', models.FloatField()),
                ('ne_lng', models.FloatField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
