from django.core.management import BaseCommand
# from subsystems.api.views import ZoneView
# from subsystems.db.model_venue import Venue
# from subsystems.db.model_zone import Zone
import os
from subsystems.db.model_zone import Zone
from subsystems.foursquare.api import FoursquareAPI

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
from conf import secret
from subsystems.foursquare.utils.foursquare_api import Foursquare

redirect_url = "http://github.com/buy-place-company/policy"


class Command(BaseCommand):
    help = 'Update zones'

    def handle(self, *args, **kwargs):
        # Construct the client object
        client = Foursquare(client_id=secret.client_id, client_secret=secret.secret_id,
                            redirect_uri=redirect_url)
        # user = client.users()
        client.set_access_token(secret.token)
        for item in client.lists(list_id='555f2c21498e177a57fd53d4')['list']['listItems']['items']:
            print( item['venue']['id'])
        # print(client.lists.additem(list_id='552fc903498ed1f7e625c7ed', params={'venueId': '40a55d80f964a52020f31ee3'}))
        sw_lat = 55.40
        sw_lng = 37.37
        ne_lat = 55.46
        ne_lng = 37.40
        # print(client.users.lists())
        FoursquareAPI.get_venue(id='502df9f2e4b047ef99bfe423')
        FoursquareAPI.new_zone_list(Zone.objects.get_small((sw_lat + ne_lat) /2, (sw_lng + ne_lng)/2))