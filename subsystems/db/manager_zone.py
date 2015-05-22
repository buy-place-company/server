from django.db import models
from conf.settings_game import ZONE_LAT_STEP, ZONE_LNG_STEP


class ZoneManager(models.Manager):
    @staticmethod
    def __normalize_axis(value):
        if value < 0:
            return value + 360
        if value >= 360:
            return value - 360
        return value

    def get_by_point(self, lat, lng):
        zones = []
        for i in range(-1, 1):
            for j in range(-1, 1):
                tmp_lat = self.__normalize_axis(lat + i*ZONE_LAT_STEP)
                tmp_lng = self.__normalize_axis(lng + j*ZONE_LNG_STEP)
                zones.append(self.get(
                    sw_lat__lt=tmp_lat,
                    ne_lat__gt=tmp_lat,
                    sw_lng__lte=tmp_lng,
                    ne_lng__gte=tmp_lng
                ))
        return zones