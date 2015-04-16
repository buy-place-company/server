import json
from django.http import HttpResponse
from conf import secret
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone
from subsystems.foursquare.foursquare_api import ServerError, Foursquare
from conf.settings_game import SettingsGame
LONG = 10.1
ERRORS = {
    '1': json.dumps({'status': 401, 'message': 'unauthorized access'}),
    '2': json.dumps({'status': 101, 'message': 'not enough args: lat and lng'}),
    '3': json.dumps({'status': 301, 'message': 'cant find zone at this coordinates'}),
    '4': json.dumps({'status': 302, 'message': 'internal foursquare error'})
}
redirect_url = "http://yandex.ru"


class ZoneView():
    def __init__(self, sw_lat, sw_lng, ne_lat, ne_lng, list_id=None):
        self.list_id = list_id
        self.ne_lat = ne_lat
        self.ne_lng = ne_lng
        self.sw_lng = sw_lng
        self.sw_lat = sw_lat

        self.client = Foursquare(client_id=secret.client_id, client_secret=secret.secret_id, redirect_uri=redirect_url)
        self._venues = None

    def create(self, name=None):
        if name is None:
            name = "auto_" + self.sw_lat + self.sw_lng + self.ne_lat + self.ne_lng
        resp = self.client.lists.add({'name': name})
        self.list_id = resp.get('id')

        venues = self.client.venue.search(sw="{0},{1}".format(self.sw_lat, self.sw_lng),
                                          ne="{0},{1}".format(self.ne_lat, self.ne_lng),
                                          categoryId=SettingsGame.DEFAULT_CATEGORIES)
        for ven in venues:
            ven['list_id'] = self.list_id
        self.save_venues()

    def venues(self, force_update=False):
        if self._venues:
            return self._venues
        if not self.list_id:
            self.create()

        if not force_update:
            venues = list(Venue.objects.filter(list_id=self.list_id).values()[:50])

        if force_update or not venues:
            try:
                venues = self.client.venue.search(sw="{0},{1}".format(self.sw_lat, self.sw_lng),
                                                  ne="{0},{1}".format(self.ne_lat, self.ne_lng),
                                                  categoryId=SettingsGame.DEFAULT_CATEGORIES)
            except ServerError:
                return None
            for ven in venues:
                ven['list_id'] = self.list_id
        self.save_venues()

        venues = list(Venue.objects.filter(list_id=self.list_id).values()[:50])
        self._venues = venues
        return venues

    def save_venues(self):
        Venue.objects.bulk_create(self.venues)


def objects_near(request):
    if not request.GET.get("access_token"):
        return HttpResponse(ERRORS['1'])
    lat = request.GET.get("lat", None)
    lng = request.GET.get("lng", None)

    if lat and lng:
        return HttpResponse(json.dumps(ERRORS['2']))

    zone_db = Zone.objects.filter(sw_lat__gt=lat).filter(ne_lat__lt=lat)\
                          .filter(sw_lng__gt=lng).filter(ne_lng__lt=lng)

    if not zone_db.get("list_id", None):
        return HttpResponse(json.dumps(ERRORS['3']))

    zone = ZoneView(sw_lat=zone_db.get("sw_lat"), sw_lng=zone_db.get("sw_lng"),
                    ne_lat=zone_db.get("ne_lat"), ne_lng=zone_db.get("ne_lng"), list_id=zone_db.get("list_id"))

    objs = zone.venues()
    if objs is not None:
        return HttpResponse(json.dumps({'status': 200, 'objects': objs}, ensure_ascii=False))
    else:
        return HttpResponse(json.dumps(ERRORS['4']))


def objects(request):
    if not request.GET.get("access_token"):
        return HttpResponse(ERRORS['1'])
    lat = request.GET.get("lat", None)
    lng = request.GET.get("lng", None)

    if lat and lng:
        return HttpResponse(json.dumps(ERRORS['2']))

    list_id = Zone.objects.filter(sw_lat__gt=lat).filter(ne_lat__lt=lat)\
                          .filter(sw_lng__gt=lng).filter(ne_lng__lt=lng).get('list_id', None)

    if not list_id:
        return HttpResponse(json.dumps(ERRORS['3']))

    objs = list(Venue.objects.filter(list_id=list_id).values()[:50])
    return HttpResponse(json.dumps({'status': 200, 'objects': objs}, ensure_ascii=False))