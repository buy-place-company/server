# -*- coding: utf-8 -*-
import time
from django.db import models


class ZoneMock:
    def __init__(self, is_active=None, parent_id=None, list_id=None, timestamp=None,
                 sw_lat=None, sw_lng=None, ne_lat=None, ne_lng=None, list_venues=None, **kwargs):
        self.is_active = is_active
        self.parent_id = parent_id
        self.list_id = list_id
        self.timestamp = timestamp
        self.sw_lat = sw_lat
        self.sw_lng = sw_lng
        self.ne_lat = ne_lat
        self.ne_lng = ne_lng
        self.list_venues = list_venues

    @staticmethod
    def create(**kwargs):
        kwargs.update({'timestamp': time.time()})
        return ZoneMock(**kwargs)

    def save(self):
        pass


class Zone(models.Model):
    is_active = models.BooleanField(default=True)
    parent_id = models.IntegerField(null=True, blank=True)
    list_id = models.CharField(max_length=255)  # unique пока боком выходит
    timestamp = models.TimeField(verbose_name="timestamp", editable=False)
    sw_lat = models.FloatField(default=0)  # Y axis
    sw_lng = models.FloatField(default=0)  # X axis
    ne_lat = models.FloatField(default=0)
    ne_lng = models.FloatField(default=0)

    # делим зону на 2 зоны, причем старая становится неактивной,
    # а новые занимают ее место
    # деление происходит по максимальной стороне
    def div(self, min_size):
        lat = abs(self.ne_lat - self.sw_lat)
        lng = abs(self.ne_lng - self.sw_lng)
        if max(lat, lng) < min_size:
            return None, None
        if lng < lat:
            middle = (self.sw_lat + self.ne_lat) / 2
            z1 = Zone.objects.create(
                parent_id=self.id,
                sw_lat=self.sw_lat,
                sw_lng=self.sw_lng,
                ne_lat=middle,
                ne_lng=self.ne_lng
            )
            z2 = Zone.objects.create(
                parent_id=self.id,
                sw_lat=middle,
                sw_lng=self.sw_lng,
                ne_lat=self.ne_lat,
                ne_lng=self.ne_lng
            )
        else:
            middle = (self.sw_lng + self.ne_lng) / 2
            z1 = Zone.objects.create(
                parent_id=self.id,
                sw_lat=self.sw_lat,
                sw_lng=self.sw_lng,
                ne_lat=self.ne_lat,
                ne_lng=middle
            )
            z2 = Zone.objects.create(
                parent_id=self.id,
                sw_lat=self.sw_lat,
                sw_lng=middle,
                ne_lat=self.ne_lat,
                ne_lng=self.ne_lng
            )
        self.is_active = False
        self.save(update_fields=['is_active'])
        return z1, z2
