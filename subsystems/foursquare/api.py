from conf import secret
from subsystems.foursquare.utils.foursquare_api import Foursquare

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

        FoursquareAPI.self.client.venues.search(params={"sw": "%f,%f" % (sw_lat, sw_lng),
                                                        "ne": "%f,%f" % (ne_lat, ne_lng)})