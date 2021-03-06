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

    @staticmethod
    def __normalize(val, step):
        precision = 10000
        aval = (abs(val * precision) - abs(val * precision) % (step * precision)) / precision
        if val < 0:
            return -aval-step, -aval
        else:
            return aval, aval+step

    def get_parent(self, lat, lng):
        lat, lng = self.__normalize_axis(lat, lng)

        try:
            return self.get(
                parent_id=None,
                sw_lat__lte=lat,
                ne_lat__gt=lat,
                sw_lng__lte=lng,
                ne_lng__gt=lng
            )
        except self.model.DoesNotExist:
            lat_min, lat_max = self.__normalize(lat, ZONE_LAT_STEP)
            lng_min, lng_max = self.__normalize(lng, ZONE_LNG_STEP)
            return self.create(
                sw_lat=lat_min,
                sw_lng=lng_min,
                ne_lat=lat_max,
                ne_lng=lng_max,
                timestamp=0
            )

    def get_zones(self, lat, lng, lat_size, lng_size):
        zones = []
        y = lat - lat_size/2
        while y < lat + lat_size/2 + ZONE_LAT_STEP:
            x = lng - lng_size/2
            while x < lng + lng_size/2 + ZONE_LNG_STEP:
                zones.append(self.get_parent(y, x))
                x += ZONE_LNG_STEP
            y += ZONE_LAT_STEP
        return zones