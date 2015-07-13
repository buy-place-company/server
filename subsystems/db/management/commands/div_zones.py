from conf.settings_game import \
    DIV_ZONE_DAYS_COUNT,\
    DIV_ZONE_AVG_COUNT,\
    DIV_ZONE_MIN_SIZE
import django
from subsystems.statistic import utils

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'div zones'

    def handle(self, *args, **kwargs):
        django.setup()
        zones = utils.statistic_analyse(DIV_ZONE_DAYS_COUNT, DIV_ZONE_AVG_COUNT)
        for z in zones:
            z1, z2 = z.div(DIV_ZONE_MIN_SIZE)
            if z1 is None or z2 is None:
                return
            # TODO: div list of venues