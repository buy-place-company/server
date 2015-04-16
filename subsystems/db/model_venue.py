# -*- coding: utf-8 -*-
from django.db import models
from .model_user import User


class Venue(models.Model):
    #system fields
    list_id = models.CharField(max_length=255)
    #to return
    name = models.CharField(max_length=30)
    id = models.CharField(max_length=255, primary_key=True)
    checkin_count = models.IntegerField(default=0)
    user_count = models.IntegerField(default=0)
    tip_count = models.IntegerField(default=0)
    category = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    lvl = models.IntegerField(default=0)
    owner = models.ForeignKey(User, null=True, blank=True)
    price = models.IntegerField(default=10000)
