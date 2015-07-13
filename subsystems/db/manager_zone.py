from django.db import models
from conf.settings_game import ZONE_LAT_STEP, ZONE_LNG_STEP


class ZoneManager(models.Manager):
    @staticmethod
    def __normalize_axis(lat, lng):
        while lat >= 90 + 360:
            lat -= 360
        while lat <= -90 - 360:
            lat += 360

        if lat > 90:
            lng += 180
            lat = 180 - lat
        elif lat < -90:
            lng += 180
            lat = 180 + lat

        while lng < -180:
            lng += 360
        while lng >= 180:
            lng -= 360

        return lat, lng

    def get_zone(self, lat, lng):
        lat, lng = self.__normalize_axis(lat, lng)

        return self.get(
            is_active=True,
            sw_lat__lt=lat,
            ne_lat__gte=lat,
            sw_lng__lt=lng,
            ne_lng__gte=lng
        )