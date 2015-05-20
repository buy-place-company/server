# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('password', models.CharField(max_length=128)),
                ('is_superuser', models.BooleanField(default=False)),
                ('email', models.EmailField(max_length=30, unique=True)),
                ('name', models.CharField(max_length=30)),
                ('signup_date', models.DateField(auto_now_add=True)),
                ('experience_count', models.BigIntegerField(default=0)),
                ('money_payed_amount', models.BigIntegerField(default=0)),
                ('money_amount', models.BigIntegerField(default=2000)),
                ('buildings_count', models.SmallIntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Venue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('title', models.CharField(max_length=30)),
                ('checkin_count', models.IntegerField(default=0)),
                ('owner', models.ForeignKey(null=True, blank=True, to='db.User')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
