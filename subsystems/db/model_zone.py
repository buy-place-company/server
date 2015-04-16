# -*- coding: utf-8 -*-
import datetime
from django.db import models


class Zone(models.Model):
    parent_id = models.IntegerField(null=True, blank=True)
    list_id = models.CharField(max_length=255)  # unique пока боком выходит
    timestamp = models.TimeField(verbose_name="timestamp", editable=False)
    sw_lat = models.FloatField(default=0)  # Y axis
    sw_lng = models.FloatField(default=0)  # X axis
    ne_lat = models.FloatField(default=0)
    ne_lng = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        self.timestamp = datetime.datetime.today()
        return super(Zone, self).save(*args, **kwargs)

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
        return z1, z2
