import os
from conf.settings_game import ZONE_LAT_STEP, ZONE_LNG_STEP

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")

import django
from subsystems.db import utils_zone

if __name__ == '__main__':
    django.setup()
    utils_zone.init_db(ZONE_LAT_STEP, ZONE_LNG_STEP)