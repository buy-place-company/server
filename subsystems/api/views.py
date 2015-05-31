import json
import datetime
import urllib.request
from django.http import HttpResponse
from conf import secret
from subsystems.db.model_user import User
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone
from subsystems.foursquare.api import Foursquare, FoursquareAPI
from conf.settings_local import SettingsLocal
from conf.secret import VK_APP_KEY
from conf.settings_game import ORDER_BY, DEFAULT_CATEGORIES, DUTY
from subsystems.foursquare.utils.foursquare_api import ServerError

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
    lat = request.GET.get("lat", None)
    lng = request.GET.get("lng", None)

    if lat is None or lng is None:
        return HttpResponse(json.dumps(ERRORS['2']))

    lat = float(lat)
    lng = float(lng)

    try:
        zone_db = Zone.objects.get_small(lat, lng)
    except Zone.DoesNotExist:
        return HttpResponse(json.dumps(ERRORS['3']))

    objs = FoursquareAPI.get_venues_from_zone(zone_db)
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


def auth_vk(request):
    if request.method != "POST":
        pass

    try:
        code = request.POST['code']
    except:
        pass

    url = \
        "https://oauth.vk.com/access_token?" + \
        "client_id=4927495&" + \
        "client_secret=%s&" % VK_APP_KEY + \
        "code=%s&" % code + \
        "redirect_uri=%s" % SettingsLocal.AUTH_URL

    try:
        conn = urllib.request.urlopen(url)
        data = json.loads(conn.read().decode('utf_8'))
    except Exception as e:
        raise e

    if 'access_token' not in data or 'user_id' not in data:
        # error
        pass

    try:
        vk_user_id = int(data['user_id'])
    except:
        raise Exception('ahaha, lulz')

    user = User.objects.create_and_auth_vk(request, vk_user_id)
    data = {
        'id': user.id,
        'id_vk': user.id_vk,
        'name': user.name
    }
    return HttpResponse(json.dumps(data), content_type="application/json")


def point_obj(request):
    try:
        lat = float(request.GET['lat'])
        lng = float(request.GET['lng'])
    except Exception as e:
        raise e

    venues = []
    for z in Zone.objects.get_by_point(lat, lng):
        for v in Venue.objects.filter(list_id=z.list_id):
            venues.append({
                'id': v.id
            })

    return HttpResponse(json.dumps(venues), content_type="application/json")