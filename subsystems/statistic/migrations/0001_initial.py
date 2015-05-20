# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Statistic',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('zoneID', models.IntegerField()),
                ('date', models.DateField(auto_now_add=True)),
                ('counter', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
