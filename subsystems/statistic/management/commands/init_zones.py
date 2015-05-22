from conf.settings_game import ZONE_LAT_STEP, ZONE_LNG_STEP
import django
from subsystems.db import utils_zone

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Update zones'

    def handle(self, *args, **kwargs):
        django.setup()
        utils_zone.init_db(ZONE_LAT_STEP, ZONE_LNG_STEP)