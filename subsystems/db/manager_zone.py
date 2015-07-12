from django.db import models
from conf.settings_game import ZONE_LAT_STEP, ZONE_LNG_STEP


class ZoneManager(models.Manager):
    @staticmethod
    def __normalize_axis(value):
        while value < 0:
            value += 360
        while value >= 360:
            value -= 360
        return value

    def get_small(self, lat, lng):
        return self.get(
            sw_lat__lt=lat,
            ne_lat__gt=lat,
            sw_lng__lte=lng,
            ne_lng__gte=lng
        )

    def get_big(self, lat, lng):
        zones = []
        for i in range(-1, 1):
            for j in range(-1, 1):
                tmp_lat = self.__normalize_axis(lat + i*ZONE_LAT_STEP)
                tmp_lng = self.__normalize_axis(lng + j*ZONE_LNG_STEP)
                zones.append(self.get_small(tmp_lat, tmp_lng))
        return zones