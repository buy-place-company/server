from django.core.management import BaseCommand

from subsystems.foursquare.api import Foursquare

from conf import secret
from conf.settings_local import SettingsLocal

# Construct the client object

client = Foursquare(client_id=secret.client_id, client_secret=secret.secret_id,
                    redirect_uri=SettingsLocal.redirect_url)

# Apply the returned access token to the client
client.set_access_token(secret.token)
# Get the user's data
user = client.users()
print(user)


class ListVenues():
    def update_list(self):
        lists = client.lists()


class Command(BaseCommand):
    help = 'Assign modal link to every webinar'

    def handle(self):
        pass
