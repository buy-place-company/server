# coding=utf-8
from datetime import datetime, timedelta
import logging
import re
import  multiprocessing as mp

from conf import secret
from conf.settings_game import DEFAULT_CATEGORIES, ZONE_UPDATE_DELTA_HOURS
from subsystems.db.model_venue import Venue
from subsystems.foursquare.utils.foursquare_api import Foursquare, FoursquareException

logger = logging.getLogger(__name__)

class Task:
    def __init__(self, venues, zone):
        self.venue_ids = [x['id'] for x in venues]
        self.zone_id = zone.id
        self.list_id = zone.list_id


def add_to_list(queue):
    while True:
        task = queue.get()
        for venue in task.venue_ids:
            item = FoursquareAPI.self.client.lists.additem(list_id=task.list_id, params={'venueId': venue})['item']
            dbvenue = FoursquareAPI.venue_from_item(item, item['venue']['id'])
            dbvenue.list_id = task.zone_id
            dbvenue.save()
            print("Added " + venue['name'])


class FoursquareAPI:
    self = None
    demon = None
    queue = None

    def __init__(self):
        self.client = Foursquare(client_id=secret.client_id, client_secret=secret.secret_id,
                                 redirect_uri=None)
        # user = client.users()
        self.client.set_access_token(secret.token)

    @staticmethod
    def venue_from_item(item, id):
        venue_raw = item['venue']
        try:
            venue = Venue.objects.get(venue_id=id)
        except Venue.DoesNotExist:
            venue = Venue.objects.create(venue_id=id)
        venue.lat = venue_raw['location']['lat']
        venue.lng = venue_raw['location']['lng']
        venue.checkin_count = venue_raw['stats']['checkinsCount']
        venue.user_count = venue_raw['stats']['usersCount']
        venue.tip_count = venue_raw['stats']['tipCount']
        venue.name = re.sub(r'[^a-zа-яA-ZА-Я ]', "", venue_raw['name'])
        # TODO: список категорий
        venue.category = venue_raw['categories'][0]['name']
        return venue

    @staticmethod
    def update_zone(zone):
        if FoursquareAPI.self is None:
            FoursquareAPI.self = FoursquareAPI()

        try:
            params = {
                    "intent": "browse",
                    "sw": "%F,%F" % (zone.sw_lat, zone.sw_lng),
                    "ne": "%F,%F" % (zone.ne_lat, zone.ne_lng),
                    "categoryId": DEFAULT_CATEGORIES,
                    "limit": 50
            }
            venues = FoursquareAPI.self.client.venues.search(params=params)['venues']
        except FoursquareException as e:
            logging.warning("[4SK] " + str(e))
            return None
        try:
            lst = FoursquareAPI.self.client.lists.add(
                {'name': 'sw{0:.3}_{1:.3}_ne{2:.3}_{3:.3}'.format(zone.sw_lat, zone.sw_lng, zone.ne_lat, zone.ne_lng)})
        except FoursquareException as e:
            logging.warning("[4SK] " + str(e))
            return None

        if not lst['list'].get('id', ''):
            logging.warning("[4SK] " + "No such list on 4sk")
            return None
        else:
            lst_id = lst['list'].get('id', '')

        zone.update(lst_id)

        if not FoursquareAPI.demon:
            queue = mp.Queue()
            FoursquareAPI.queue = queue
            FoursquareAPI.demon = mp.Process(target=add_to_list(queue))

        queue.put(Task(venues, zone))

        return zone

    @staticmethod
    def get_venue(id):
        if not FoursquareAPI.self:
            FoursquareAPI.self = FoursquareAPI()
        item = FoursquareAPI.self.client.venues(venue_id=id)
        venue = FoursquareAPI.venue_from_item(item, item['venue']['id'])
        venue.save()
        return venue

    @staticmethod
    def get_venues_from_zone(zone):
        if not FoursquareAPI.self:
            FoursquareAPI.self = FoursquareAPI()

        if zone.list_id is None:
            logger.warning("[ZONE] List for zone doesnt exist. zid: %d" % zone.id)
            FoursquareAPI.update_zone(zone)

        if zone.timestamp + timedelta(hours=ZONE_UPDATE_DELTA_HOURS).total_seconds() < datetime.now().timestamp():
            logger.warning("[ZONE] Timestamp has expired. zid: %d" % zone.id)
            FoursquareAPI.update_zone(zone)

        return list(Venue.objects.filter(list_id=zone.id))
