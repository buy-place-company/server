import datetime
from django.core.management import BaseCommand
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone


from conf import secret
from subsystems.foursquare.foursquare_api import Foursquare, ServerError

redirect_url = "http://yandex.ru/"


class ZoneView():
    def __init__(self, client, list_id=None, lat=None, lng=None, venues=None):
        self.client = client
        self.lng = lng
        self.lat = lat
        self.list_id = list_id
        self.venues = venues

    def create(self, name):
        return self.client.lists.add({'name': name})

    def load_venues_db(self):
        self.venues = Venue.objects.filter(list_id=self.list_id)

    def load_venues_foursquare(self):
        try:
            return self.client.lists()
        except ServerError:
            # Log("4sk server acquired")
            return None

    def save_venues(self, objects):
        Venue.objects.bulk_create(objects)

    def save(self):
        timestamp = datetime.datetime.now().timestamp()
        Zone.objects.create()


class Command(BaseCommand):
    help = 'Update zones'

    def handle(self, *args, **kwargs):
        # Construct the client object
        client = Foursquare(client_id=secret.client_id, client_secret=secret.secret_id,
                            redirect_uri=redirect_url)

        # Apply the returned access token to the client
        client.set_access_token(secret.token)
        # Get the user's data
        # user = client.users()
        zone = ZoneView(client)
        print(zone.create("test list"))
        #print(zone.load_objects())
        return