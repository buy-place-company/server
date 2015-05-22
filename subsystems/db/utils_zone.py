import datetime
from subsystems.db.model_zone import Zone


def init_db(lat_step, lng_step):
    for x in range(0, 360, lng_step):
        for y in range(-90, 90, lat_step):
            Zone.objects.create(
                sw_lat=y,
                sw_lng=x,
                ne_lat=y+lat_step,
                ne_lng=x+lng_step,
                timestamp=datetime.datetime.now()
            )