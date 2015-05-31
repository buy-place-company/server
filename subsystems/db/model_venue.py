# -*- coding: utf-8 -*-
from django.db import models
from .model_user import User
import re
from json import JSONEncoder

BASE_COST = 300
BASE_INCOME = 100


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
    lvl = models.IntegerField(default=0)
    owner = models.ForeignKey(User, null=True, blank=True)
    price = models.IntegerField(default=10000)
    lat = models.FloatField(default=0)
    lng = models.FloatField(default=0)

    # private information
    loot = models.IntegerField(null=True)

    def serialize(self):
        return {
            "id": self.venue_id,
            "stats": {
                "checkinsCount": self.checkin_count,
                "usersCount": self.user_count,
                "tipCount": self.tip_count
            },
            "name": self.name,
            "category": self.category,
            "lvl": self.lvl,
            "owner": self.owner.serialize(),
            "latitude": self.lat,
            "longitude": self.lng,
            "max_loot": self.max_loot,
            "income": self.income,
            "expense": self.expense,
            "sell_price": self.npc_sell_price,
            "buy_price": self.npc_buy_price,
            "upgrade_price": self.upgrade_price,
            "loot": self.loot if self.loot else 0
        }

    @property
    def max_loot(self):
        return self.lvl ** 1.1

    @property
    def income(self):
        return BASE_INCOME * self.lvl * (1.1 ** (self.lvl - 1))

    @property
    def npc_buy_price(self):
        return self.expense * 1.1

    @property
    def npc_sell_price(self):
        return self.expense * 0.9

    @property
    def expense(self):
        upgrades_price = BASE_COST * 2 * round(1.5 ** self.lvl)
        return self.checkin_count * 10000 + self.user_count * 1000 + upgrades_price

    @property
    def upgrade_price(self):
        return BASE_COST*(1.5 ** (self.lvl - 1))
