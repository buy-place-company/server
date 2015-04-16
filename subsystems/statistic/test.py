import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")

import django
from subsystems.db.model_zone import Zone
from subsystems.statistic.utils import statistic_analyse

if __name__ == '__main__':
    django.setup()
    """
    z = Zone.objects.get(id=1)
    z.sw_lat = 10
    z.sw_lng = 20
    z.ne_lat = 30
    z.ne_lng = 40
    z.save()
    """

    zones = statistic_analyse(1, 3)
    for z in zones:
        z.div(5)