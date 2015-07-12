import datetime
from subsystems.db.model_zone import Zone


def init_db(lat_step, lng_step):
    x = 0
    while x < 360:
        y = -90
        while y < 90:
            Zone.objects.create(
                sw_lat=y,
                sw_lng=x,
                ne_lat=round(y+lat_step, 1),
                ne_lng=round(x+lng_step, 1),
                timestamp=0
            )
            y += lng_step
        x += lat_step