from conf.settings_game import ZONE_LAT_STEP, ZONE_LNG_STEP
import django
from subsystems.statistic import utils

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Save statistic'

    def handle(self, *args, **kwargs):
        django.setup()
        utils.statistic_save()