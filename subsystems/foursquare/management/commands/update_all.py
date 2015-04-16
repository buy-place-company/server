# import datetime
# from django.core.management import BaseCommand
# from subsystems.db.model_venue import Venue
# from subsystems.db.model_zone import Zone
#
#
# from conf import secret
# from subsystems.foursquare.foursquare_api import Foursquare, ServerError
#
# redirect_url = "http://yandex.ru/"
#
# class Command(BaseCommand):
#     help = 'Update zones'
#
#     def handle(self, *args, **kwargs):
#         # Construct the client object
#         client = Foursquare(client_id=secret.client_id, client_secret=secret.secret_id,
#                             redirect_uri=redirect_url)
#
#         # Apply the returned access token to the client
#         client.set_access_token(secret.token)
#         # Get the user's data
#         # user = client.users()
#         zone = ZoneView(client)
#         print(zone.create("test list"))
#         #print(zone.load_objects())
#         return