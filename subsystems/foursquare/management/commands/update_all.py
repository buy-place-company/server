import datetime
from django.core.management import BaseCommand
from subsystems.api.views import ZoneView
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone


from conf import secret
from subsystems.foursquare.foursquare_api import Foursquare, ServerError

redirect_url = "http://github.com/buy-place-company/policy"


class Command(BaseCommand):
    help = 'Update zones'

    def handle(self, *args, **kwargs):
        # Construct the client object
        client = Foursquare(client_id=secret.client_id, client_secret=secret.secret_id,
                            redirect_uri=redirect_url)
        # print(client.oauth.auth_url())
        # Apply the returned access token to the client
        # Get the user's data
        # user = client.users()
        #zone = ZoneView(client)
        client.set_access_token(secret.token)
        # client.lists.add({'name':"test list"})
        print (client.lists({'name': 'test list'}))
        #print(zone.load_objects())
        return