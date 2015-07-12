import json
import datetime
import urllib.request
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from conf import secret
from subsystems.api.errors import GameError, NoMoneyError, HasOwnerAlready, UHaveIt, UDontHaveIt
from subsystems.api.utils import JSONResponse
from subsystems.db.model_user import User
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone
from subsystems.foursquare.api import Foursquare, FoursquareAPI
from conf.settings_local import SettingsLocal
from conf.secret import VK_APP_KEY, VK_APP_ID
from conf.settings_game import ORDER_BY, DEFAULT_CATEGORIES, DUTY
from subsystems.foursquare.utils.foursquare_api import ServerError


redirect_url = "http://yandex.ru"
# TODO: security!!!


class ZoneView:
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


class VenueView:
    def __init__(self, venue_id):
        self.venue = Venue.objects.get(venue_id=venue_id)

    def __getitem__(self, item):
        return self.venue.get(item)

    def buy(self, user):
        if user.cash < self.venue.price:
            raise NoMoneyError

        if self.venue.owner == user:
            raise UHaveIt

        if self.venue.owner:
            raise HasOwnerAlready

        self.venue.owner = user
        user.cash -= self.venue.price
        user.score += self.venue.price
        user.buildings_count += 1
        user.save()
        self.venue.save()

    def sell(self, user):
        if self.venue.owner != user:
            raise UDontHaveIt

        self.venue.owner = None
        user.cash += self.venue.price
        user.score -= self.venue.price
        user.buildings_count -= 1
        user.save()
        self.venue.save()

    def upgrade(self, user):
        price = self.venue.price * (1 + self.venue.lvl ** 1.1) / (1 + self.venue.lvl) * (1 - DUTY)

        if self.venue.owner != user:
            raise UDontHaveIt

        if user.cash < price:
            raise NoMoneyError

        user.cash -= price
        user.score += price
        user.save()
        self.venue.save()


@csrf_exempt
def objects(request):
    try:
        lat = float(request.GET["lat"])
        lng = float(request.GET["lng"])
    except:
        return GameError('2')

    try:
        zone_db = Zone.objects.get_small(lat, lng)
    except Zone.DoesNotExist:
        return GameError('3')

    objs = FoursquareAPI.get_venues_from_zone(zone_db)
    if objs is not None:
        return JSONResponse.serialize(objs, aas='places', status=200)
    else:
        return GameError('4')


@csrf_exempt
def obj(request):
    try:
        venue_id = request.GET.get("venue_id", None)
    except ValueError:
        return GameError('9')

    if venue_id is None:
        return GameError('9')

    try:
        _obj = Venue.objects.get(venue_id=venue_id)
    except Venue.DoesNotExist:
        return GameError('3')
    except Venue.MultipleObjectsReturned:
        return GameError('8')

    if _obj is not None:
        return JSONResponse.serialize(_obj, aas='objects', status=200)
    else:
        return GameError('4')


@csrf_exempt
def user_objects(request):
    if not request.user.is_authenticated():
        return GameError('1')

    objs = Venue.objects.filter(owner=request.user)
    return JSONResponse.serialize(list(objs), aas='objects', status=200, public=False)


@csrf_exempt
def object_action(request):
    if not request.user.is_authenticated():
        return GameError('1')

    action = request.POST.get('action', None)
    venue_id = request.POST.get('venue_id', None)

    if not action or not hasattr(VenueView, action):
        return GameError('5')

    if not venue_id:
        return GameError('6')

    try:
        venue = VenueView(venue_id)
    except Venue.DoesNotExists:
        return GameError('7')

    try:
        getattr(venue, action)(request.user)
    except NoMoneyError:
        return GameError('11')
    except HasOwnerAlready:
        return GameError('12')
    except UHaveIt:
        return GameError('13')
    except UDontHaveIt:
        return GameError('14')

    return JSONResponse.serialize(request.user, aas='user', status=200, public=False)


@csrf_exempt
def profile(request):
    if not request.user.is_authenticated():
        return GameError('1')

    return JSONResponse.serialize(request.user, aas='user', status=200, public=False)


# noinspection PyTypeChecker
@csrf_exempt
def rating(request):
    if not request.user.is_authenticated():
        return GameError('1')

    offset = request.GET.get('offset', 0)
    order_by = ORDER_BY.get(request.GET.get('param', 'exp'), None)

    if order_by is None:
        return GameError('9')

    users = User.objects.all().order_by("-" + order_by)[offset:offset + 20]
    return JSONResponse.serialize(users, aas='users', status=200,
                                  user={'name': request.user.name, order_by: getattr(request.user, order_by),
                                        'pos': 2342352353452345234})


@csrf_exempt
def auth_vk(request):
    url = \
        "https://oauth.vk.com/access_token?" + \
        "client_id=%s&" % VK_APP_ID + \
        "client_secret=%s&" % VK_APP_KEY + \
        "code=%s&" % request.GET.get('code', '') + \
        "redirect_uri=%s" % SettingsLocal.AUTH_REDIRECT_URL

    try:
        conn = urllib.request.urlopen(url)
        data = json.loads(conn.read().decode('utf_8'))
    except:
        return GameError('10')

    if 'access_token' not in data or 'user_id' not in data:
        return GameError('10')

    try:
        vk_user_id = int(data['user_id'])
    except:
        return GameError('10')

    user = User.objects.create_and_auth_vk(request, vk_user_id)
    data = {
        'id': user.id,
        'id_vk': user.id_vk,
        'name': user.name
    }
    return HttpResponse(json.dumps(data), content_type="application/json")


def test(request):
    return HttpResponse(render_to_string("test.html", {}))
