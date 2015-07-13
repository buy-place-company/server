from datetime import datetime, timedelta
import logging
import re
from conf import secret
from conf.settings_game import DEFAULT_CATEGORIES
from subsystems.db.model_venue import Venue
from subsystems.foursquare.utils.foursquare_api import Foursquare, FoursquareException
logger = logging.getLogger(__name__)
UPDATE_ZONE_DELTA_TIME = 12


class FoursquareAPI:
    self = None

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
        # print("Added " + venue.name)
        return venue

    @staticmethod
    def update_zone(zone):
        if FoursquareAPI.self is None:
            FoursquareAPI.self = FoursquareAPI()

        try:
            venues = FoursquareAPI.self.client.venues.search(
                params={"intent": "browse", "sw": "%F,%F" % (zone.sw_lat, zone.sw_lng),
                        "ne": "%F,%F" % (zone.ne_lat, zone.ne_lng),
                        "categoryId": DEFAULT_CATEGORIES})['venues']
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

        for venue in venues:
            if venue.get('id', ''):
                item = FoursquareAPI.self.client.lists.additem(list_id=lst_id, params={'venueId': venue['id']})['item']
                dbvenue = FoursquareAPI.venue_from_item(item, item['venue']['id'])
                dbvenue.list_id = zone.id
                dbvenue.save()

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
        logger.info("\033[22;31m%s\033[0;0m" % "[ZONE] List for this zone doesnt exist.")
        if not FoursquareAPI.self:
            FoursquareAPI.self = FoursquareAPI()

        if zone.timestamp + timedelta(hours=UPDATE_ZONE_DELTA_TIME).total_seconds() < datetime.now().timestamp():
            logger.warning("[ZONE] Timestamp has expired. zid: %d" % zone.id)
            FoursquareAPI.update_zone(zone)

        if not zone.list_id:
            logger.warning("[ZONE] List for this zone doesnt exist.")
            FoursquareAPI.update_zone(zone)

        lst = list(Venue.objects.filter(list_id=zone.id))
        return lst