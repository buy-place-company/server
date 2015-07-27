# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
import hashlib
from django.db.models import ForeignKey

from django.db import models
from subsystems.db.model_user import User


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
    # to return
    name = models.CharField(max_length=255)
    # TODO: перефигачить везде на просто id
    venue_id = models.CharField(max_length=255, unique=True)
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

    # For pushes
    @property
    def push_id(self):
        return self.venue_id

    @property
    def check_sum(self):
        return ''.join([str(self.owner.id if self.owner else ''), str(self.lvl)])

    # General
    def serialize(self, is_public=True, **kwargs):
        user = kwargs.pop('user_owner', None)
        is_favorite = Bookmark.objects.filter(user=user, venue_id=self.venue_id)
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
            "is_favorite": True if is_favorite else False,
            "buy_price": round(self.npc_buy_price, 1)
        }
        if self.owner is not None and (not is_public or self.owner == user):
            response.update({
                "max_loot": round(self.max_loot, 1),
                "sell_price": round(self.npc_sell_price, 1),
                "upgrade_price": round(self.upgrade_price, 1),
                # "expense": self.expense,
                "loot": self.loot or 0,
                "income": self.income,
                "consumption": self.consumption
            })

        return response

    @property
    def max_loot(self):
        return self.income * (24 + self.lvl ** 1.45)

    @property
    def _base_cost(self):
        return ((self.checkin_count * 5) ** 0.5) * 100 + self.user_count * 1000

    @property
    def npc_buy_price(self):
        return round(self.expense * 1.1)

    @property
    def npc_sell_price(self):
        return round(self.expense * 0.9)

    @property
    def expense(self):
        upgrades_price = 0
        for lvl in range(0, self.lvl, 1):
            upgrades_price += self.get_upgrade_price(lvl)
        return round(self._base_cost + self.income * 24 + upgrades_price)

    @property
    def upgrade_price(self):
        return self.get_upgrade_price(self.lvl)

    def get_upgrade_price(self, lvl):
        return round((self._base_cost ** 0.8) * (1.4 ** (lvl - 1)))

    @property
    def income(self):
        return round(self._base_cost ** 0.6) * (1 + 1.4 ** self.lvl)

    @property
    def consumption(self):
        return round(BASE_INCOME * 10 + 0.1 * self.income)
        # return round(BASE_INCOME * (1.1 ** (self.lvl - 1)) - BASE_INCOME / 2)

    def update(self):
        update_time = self.last_update + timedelta(seconds=TIME_DELTA).total_seconds()
        now = datetime.now().timestamp()
        div = now - update_time
        if self.owner and div > 0:
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
        # self.last_update = datetime.now().timestamp()
        super(Venue, self).save(*args, **kwargs)


class Bookmark(models.Model):
    # system fields
    user = ForeignKey(User)
    venue = ForeignKey(Venue, to_field='venue_id')
    push_check_sum = models.CharField(max_length=33)
    is_autocreated = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        m = hashlib.md5()
        m.update(self.venue.check_sum.encode('utf-8'))
        self.push_check_sum = m.hexdigest()
        super(Bookmark, self).save(*args, **kwargs)

    def serialize(self, user_owner=None, **kwargs):
        return self.venue.serialize(user_owner=user_owner, **kwargs)
