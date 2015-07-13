# -*- coding: utf-8 -*-
from datetime import datetime

from django.db import models

from subsystems.db.manager_zone import ZoneManager


class Zone(models.Model):
    is_active = models.BooleanField(default=True)
    parent_id = models.IntegerField(null=True, blank=True)
    list_id = models.CharField(max_length=255, null=True)  # unique пока боком выходит
    timestamp = models.FloatField(default=0, editable=False)
    sw_lat = models.FloatField(default=0)  # Y axis
    sw_lng = models.FloatField(default=0)  # X axis
    ne_lat = models.FloatField(default=0)
    ne_lng = models.FloatField(default=0)

    # lat >= sw_lat && lng >= sw_lng
    # lat <= ne_lat && lng <= ne_lng

    objects = ZoneManager()

    def update(self, list_id):
        self.list_id = list_id
        self.timestamp = datetime.now().timestamp()
        self.save()

    # делим зону на 2 зоны, причем старая становится неактивной,
    # а новые занимают ее место
    # деление происходит по максимальной стороне
    def div(self, min_size):
        lat = abs(self.ne_lat - self.sw_lat)
        lng = abs(self.ne_lng - self.sw_lng)
        if max(lat, lng) < min_size:
            return None, None
        parent_id = self.parent_id is None and self.id or self.parent_id
        if lng < lat:
            middle = (self.sw_lat + self.ne_lat) / 2
            z1 = Zone.objects.create(
                parent_id=parent_id,
                sw_lat=self.sw_lat,
                sw_lng=self.sw_lng,
                ne_lat=middle,
                ne_lng=self.ne_lng
            )
            z2 = Zone.objects.create(
                parent_id=parent_id,
                sw_lat=middle,
                sw_lng=self.sw_lng,
                ne_lat=self.ne_lat,
                ne_lng=self.ne_lng
            )
        else:
            middle = (self.sw_lng + self.ne_lng) / 2
            z1 = Zone.objects.create(
                parent_id=parent_id,
                sw_lat=self.sw_lat,
                sw_lng=self.sw_lng,
                ne_lat=self.ne_lat,
                ne_lng=middle
            )
            z2 = Zone.objects.create(
                parent_id=parent_id,
                sw_lat=self.sw_lat,
                sw_lng=middle,
                ne_lat=self.ne_lat,
                ne_lng=self.ne_lng
            )
        self.is_active = False
        self.save(update_fields=['is_active'])
        return z1, z2

    def has_point(self, lat, lng):
        return self.sw_lat < lat <= self.ne_lat and self.sw_lng <= lng < self.ne_lng