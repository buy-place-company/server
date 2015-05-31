# -*- coding: utf-8 -*-
from django.db import models
from .model_user import User
import re
from json import JSONEncoder


class Venue(models.Model):
    # system fields
    list_id = models.CharField(max_length=255)
    #to return
    name = models.CharField(max_length=255)
    venue_id = models.CharField(max_length=255, primary_key=True)
    checkin_count = models.IntegerField(default=0)
    user_count = models.IntegerField(default=0)
    tip_count = models.IntegerField(default=0)
    category = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    lvl = models.IntegerField(default=0)
    owner = models.ForeignKey(User, null=True, blank=True)
    price = models.IntegerField(default=10000)

    def serialize(self):
        return {"id": self.venue_id,
                "stats": {
                    "checkinsCount": self.checkin_count,
                    "usersCount": self.user_count,
                    "tipCount": self.tip_count
                },
                "name": self.name,
                "category": self.category,
                "type": self.type,
                "lvl": 10,
                "owner": {},
                "latitude": 44.4,
                "longitude": 38.1,
                "max_loot": 900,
                "income": 12,
                "expense": 15,
                "buy_price": null,
                "update_price": 1500,
                "sell_price": 500,
                "deal_price": 750,
                "loot": 412
                }
