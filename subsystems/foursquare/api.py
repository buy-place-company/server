from conf import secret
from conf.settings_game import DEFAULT_CATEGORIES
from subsystems.db.model_venue import VenueMock
from subsystems.db.model_zone import ZoneMock
from subsystems.foursquare.utils.foursquare_api import Foursquare, FoursquareException

__author__ = 'Ruslan'


class FoursquareAPI:
    self = None

    def __init__(self):
        self.client = Foursquare(client_id=secret.client_id, client_secret=secret.secret_id,
                                 redirect_uri=None)
        # user = client.users()
        self.client.set_access_token(secret.token)

    @staticmethod
    def new_zone(sw_lat=None, sw_lng=None, ne_lat=None, ne_lng=None):
        if sw_lat is None or sw_lng is None or ne_lat is None or ne_lng is None:
            return None

        if FoursquareAPI.self is None:
            FoursquareAPI.self = FoursquareAPI()

        venues = FoursquareAPI.self.client.venues.search(params={"intent": "browse", "sw": "%F,%F" % (sw_lat, sw_lng),
                                              "ne": "%F,%F" % (ne_lat, ne_lng),
                                              "categotyId": DEFAULT_CATEGORIES})['venues']
        try:
            lst = FoursquareAPI.self.client.lists.add({'name': 'sw{0:.3}_{1:.3}_ne{2:.3}_{3:.3}'.format(sw_lat, sw_lng, ne_lat, ne_lng)})
        except FoursquareException:
            print("Zone with such corrds exists already")
            return None

        if not lst['list'].get('id', ''):
            print("No list created")
            return None
        else:
            lst_id = lst['list'].get('id', '')

        print(lst_id)
        zone = ZoneMock.create(sw_lat=sw_lat, sw_lng=sw_lng, ne_lat=ne_lat, ne_lng=ne_lng, list_id=lst_id, is_activate=0)

        for venue in venues:
            if venue.get('id', ''):
                item = FoursquareAPI.self.client.lists.additem(list_id=lst_id, params={'venueId': venue['id']})['item']
                venue_raw = item['venue']
                venue = VenueMock()
                venue.lat = venue_raw['location']['lat']
                venue.lng = venue_raw['location']['lng']
                venue.stats['checkin_count'] = venue_raw['stats']['checkinsCount']
                venue.stats['user_count'] = venue_raw['stats']['usersCount']
                venue.stats['tip_count'] = venue_raw['stats']['tipCount']
                venue.set_name(venue_raw['name'])
                venue.id = item['id']
                venue.save()

        return zone