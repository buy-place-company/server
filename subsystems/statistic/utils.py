import redis
import datetime
from subsystems.statistic.models import Statistic
from subsystems.db.models import Zone


def statistic_add_hit(zone_id):
    r = redis.Redis(unix_socket_path='/var/run/redis/redis.sock', db=0)
    r.incr("c{}".format(zone_id))


def statistic_save():
    r = redis.Redis(unix_socket_path='/var/run/redis/redis.sock', db=0)

    for zone in Zone.objects.all():
        try:
            counter_b = r.getset("c{}".format(zone.id), 0)
            counter = counter_b is None and 0 or int(counter_b)
            if counter > 0:
                Statistic.objects.create(zone_id=zone.id, counter=counter)
        except Exception as e:
            print(e)


# возвращает зоны, у которых средний показатель за days_count больше или равен avg_counter_limit
def statistic_analyse(days_count, avg_counter_limit):
    after_date = datetime.datetime.now() - datetime.timedelta(days=days_count)
    zones = []

    for zone in Zone.objects.all():
        avg_counter = 0
        for stat in Statistic.objects.filter(zone_id=zone.id, date__gt=after_date):
            avg_counter += stat.counter
        avg_counter /= days_count

        if avg_counter >= avg_counter_limit:
            zones.append(zone)

    return zones