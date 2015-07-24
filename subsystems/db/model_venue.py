# -*- coding: utf-8 -*-
from datetime import timedelta, datetime

from django.db import models

from .model_user import User

BASE_COST = 300
BASE_INCOME = 100
TIME_DELTA = 30

class VenueManager(models.Manager):
    def get_queryset(self):
        ret = super(VenueManager, self).get_queryset()
        set = ret.filter(owner_id__gte=0,
                         last_update__lte=(datetime.now().timestamp() - timedelta(seconds=TIME_DELTA).total_seconds()))
        for obj in set:
                obj.update()
        return ret


class Venue(models.Model):
    # system fields
    list_id = models.CharField(max_length=255)
    last_update = models.IntegerField(default=0)
    #to return
    name = models.CharField(max_length=255)
    venue_id = models.CharField(max_length=255, primary_key=True)
    checkin_count = models.IntegerField(default=0)
    user_count = models.IntegerField(default=0)
    tip_count = models.IntegerField(default=0)
    category = models.CharField(max_length=255)
    lvl = models.IntegerField(default=0)
    owner = models.ForeignKey(User, null=True, blank=True)
    lat = models.FloatField(default=0)
    lng = models.FloatField(default=0)

    # private information
    loot = models.IntegerField(default=0)

    # Managers
    updatable = VenueManager()
    objects = VenueManager()

    def serialize(self, is_public=True, **kwargs):
        user = kwargs.pop('user_owner', None)
        response = {
            "id": self.venue_id,
            "stats": {
                "checkinsCount": self.checkin_count,
                "usersCount": self.user_count,
                "tipCount": self.tip_count
            },
            "name": self.name,
            "category": self.category,
            "lvl": self.lvl,
            "owner": self.owner.serialize(user_owner=user) if self.owner else None,
            "latitude": round(self.lat, 3),
            "longitude": round(self.lng, 3),
        }
        print(self.owner, self.owner == user)
        if self.owner is not None and (not is_public or self.owner == user):
            response.update({
                "max_loot": round(self.max_loot, 1),
                "sell_price": round(self.npc_sell_price, 1),
                "buy_price": round(self.npc_buy_price, 1),
                "upgrade_price": round(self.upgrade_price, 1),
                # "expense": self.expense,
                "loot": self.loot or 0,
                "income": self.income,
                "consumption": self.consumption
            })

        if self.owner is None:
            response.update({"buy_price": round(self.npc_buy_price, 1)})

        return response

    @property
    def max_loot(self):
        return round(3 * self.income * (1.1 ** self.lvl))

    @property
    def income(self):
        return round(BASE_INCOME / 10 + BASE_INCOME * self.lvl * (1.1 ** (self.lvl - 1)) + 10 * self.checkin_count + self.user_count * 10)

    @property
    def npc_buy_price(self):
        return round(self.expense * 1.1)

    @property
    def npc_sell_price(self):
        return round(self.expense * 0.9)

    @property
    def expense(self):
        upgrades_price = BASE_COST * 2 * round(1.5 ** self.lvl)
        return round(self.checkin_count * 1000 + self.user_count * 100 + upgrades_price + self.income * 24)

    @property
    def upgrade_price(self):
        return round(BASE_COST*(1.5 ** (self.lvl - 1)))

    @property
    def consumption(self):
        return round(BASE_INCOME * (1.1 ** (self.lvl - 1)) - BASE_INCOME / 2)

    def update(self):
        update_time = self.last_update + timedelta(seconds=TIME_DELTA).total_seconds()
        now = datetime.now().timestamp()
        div = now - update_time
        if self.owner:
            if self.owner.cash + self.income > self.consumption:
                inc = round((self.income - self.consumption) % 3600 * div)
                if inc > 0:
                    if self.max_loot >= self.loot + inc:
                        self.loot += inc
                    else:
                        self.loot = self.max_loot
                else:
                    self.owner.cash += inc
            else:
                self.owner.cash = 0
            self.last_update = datetime.now().timestamp()
            self.save()

    def save(self, *args, **kwargs):
        self.last_update = datetime.now().timestamp()
        super(Venue, self).save(*args, **kwargs)
