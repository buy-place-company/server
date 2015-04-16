import json
import datetime
from django.http import HttpResponse, Http404
from conf import secret
from subsystems.db.model_user import User
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone
from subsystems.foursquare.foursquare_api import ServerError, Foursquare
from conf.settings_game import ORDER_BY, DEFAULT_CATEGORIES, DUTY
LONG = 10.1
ERRORS = {
    '1': {'status': 401, 'message': 'unauthorized access'},
    '2': {'status': 101, 'message': 'not enough args: lat and lng'},
    '3': {'status': 301, 'message': 'cant find zone at this coordinates'},
    '4': {'status': 302, 'message': 'internal foursquare error'},
    '5': {'status': 101, 'message': 'not enough args: action'},
    '6': {'status': 101, 'message': 'building id isnt specified'},
    '7': {'status': 302, 'message': 'no such building'},
    '8': {'status': 103, 'message': 'Smth wrong'},
    '9': {'status': 104, 'message': 'Invalid param specified.'}
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
                                                  categoryId=DEFAULT_CATEGORIES)
            except ServerError:
                return None
            for ven in venues:
                ven['list_id'] = self.list_id
        self.save_venues()

        venues = list(Venue.objects.filter(list_id=self.list_id).values()[:50])
        self._venues = venues
        return venues

    def save_venues(self):
        obj = Zone.objects.get('list_id', None)
        obj.timestamp = datetime.datetime.now()
        obj.save()
        Venue.objects.bulk_create(self.venues)


class VenueView():
    def __init__(self, id):
        self.venue = Venue.objects.get(id=id)

    def __getitem__(self, item):
        return self.venue.get(item)

    def buy(self, user):
        if user.money_amount > self.venue.price and not self.venue.owner:
            self.venue.owner = user.id
            user.money_amount -= self.venue.price
            user.money_payed_amount += self.venue.price
            self.venue.save()
            return True
        else:
            return False

    def sell(self, user):
        if self.venue.owner == user.id:
            self.venue.owner = 0
            user.money_amount += self.venue.price * (1 - DUTY)
            user.money_payed_amount -= self.venue.price
            self.venue.save()
            return True
        else:
            return False

    def upgrade(self, user):
        if self.venue.owner == user.id:
            user.money_amount -= self.venue.price * (1 + self.venue.lvl ** 1.1) / (1 + self.venue.lvl)\
                * (1 - DUTY)
            user.money_payed_amount += self.venue.price
            self.venue.save()
            return True
        else:
            return False


def objects_near(request):
    #if not request.user.is_authenticated():
    #    return HttpResponse(json.dumps(ERRORS['1']))
    lat = request.GET.get("lat", None)
    lng = request.GET.get("lng", None)

    if lat is None or lng is None:
        return HttpResponse(json.dumps(ERRORS['2']))

    try:
        zone_db = Zone.objects.filter(sw_lat__lt=lat).filter(ne_lat__gt=lat)\
                              .filter(sw_lng__lt=lng).filter(ne_lng__gt=lng).get()
    except Zone.DoesNotExist:
        return HttpResponse(json.dumps(ERRORS['3']))

    if not zone_db.list_id:
        return HttpResponse(json.dumps(ERRORS['3']))

    zone = ZoneView(sw_lat=zone_db.get("sw_lat"), sw_lng=zone_db.get("sw_lng"),
                    ne_lat=zone_db.get("ne_lat"), ne_lng=zone_db.get("ne_lng"), list_id=zone_db.get("list_id"))

    objs = zone.venues()
    if objs is not None:
        return HttpResponse(json.dumps({'status': 200, 'objects': objs}, ensure_ascii=False))
    else:
        return HttpResponse(json.dumps(ERRORS['4']))


def user_objects(request):
    if not request.user.is_authenticated():
        return HttpResponse(ERRORS['1'])

    objs = Venue.objects.filter(owner=request.user.id).values()

    return HttpResponse(json.dumps({'status': 200, 'objects': objs}, ensure_ascii=False))


def object_action(request):
    if not request.user.is_authenticated():
        return HttpResponse(ERRORS['1'])

    action = request.POST.get('action', None)
    id = request.POST.get('id', None)

    if not action or not hasattr(VenueView, action):
        return HttpResponse(ERRORS['5'])

    if not id:
        return HttpResponse(ERRORS['6'])

    try:
        venue = VenueView(id)
    except Venue.DoesNotExists as e:
        return HttpResponse(json.dumps(ERRORS[7]))

    if getattr(venue, action)():
        return HttpResponse(json.dumps({'status': 200, 'cache': request.user.money_amount}, ensure_ascii=False))
    else:
        return HttpResponse(json.dumps(ERRORS['8'], ensure_ascii=False))


# noinspection PyTypeChecker
def rating(request):
    if not request.user.is_authenticated():
        return HttpResponse(ERRORS['1'])

    offset = request.GET.get('offset', 0)
    order_by = ORDER_BY.get(request.GET.get('param', 'exp'), None)

    if order_by is None:
        return HttpResponse(ERRORS['9'])

    users = User.objects.all().order_by("-" + order_by)[offset:offset+20]
    users_to_return = [{'name': user.name, order_by: getattr(user, order_by)} for user in users]

    return HttpResponse(json.dumps({'status': 200, 'objects': users_to_return,
                                    'user': {'name': request.user.name, order_by: getattr(request.user, order_by),
                                             'pos': 2342352353452345234}}))