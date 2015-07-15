import json
import logging
import urllib.request
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from subsystems._auth import logout
from subsystems.api.errors import GameError, NoMoneyError, HasOwnerAlready, UHaveIt, UDontHaveIt
from subsystems.api.utils import JSONResponse, VenueView
from subsystems.db.model_user import User
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone
from subsystems.foursquare.api import FoursquareAPI
from conf.settings_local import SettingsLocal
from conf.secret import VK_APP_KEY, VK_APP_ID
from conf.settings_game import ORDER_BY, ZONE_LNG_STEP, ZONE_LAT_STEP

logger = logging.getLogger(__name__)


@csrf_exempt
def zone_venues(request):
    print(request.user.name)
    try:
        lat = float(request.GET["lat"])
        lng = float(request.GET["lng"])
        lat_size = min(request.GET.get("lat_size", ZONE_LAT_STEP), 10*ZONE_LAT_STEP)
        lng_size = min(request.GET.get("lng_size", ZONE_LNG_STEP), 10*ZONE_LNG_STEP)
    except (KeyError, ValueError, TypeError):
        return GameError('2')

    venues = []
    for z in Zone.objects.get_zones(lat, lng, lat_size, lng_size):
        venues.extend(FoursquareAPI.get_venues_from_zone(z))

    return JSONResponse.serialize(venues, aas='venues', status=200)


@csrf_exempt
def venue_info(request):
    try:
        venue_id = request.GET["venue_id"]
    except KeyError:
        return GameError('9')

    try:
        venue = Venue.objects.get(venue_id=venue_id)
    except Venue.DoesNotExist:
        return GameError('3')
    except Venue.MultipleObjectsReturned:
        return GameError('8')

    if venue is None:
        return GameError('4')

    return JSONResponse.serialize(venue, aas='objects', status=200)


@csrf_exempt
def venue_action(request):
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
def user_profile(request):
    if not request.user.is_authenticated():
        return GameError('1')

    return JSONResponse.serialize(request.user, aas='user', status=200, public=False)


@csrf_exempt
def user_venues(request):
    if not request.user.is_authenticated():
        return GameError('1')

    objs = Venue.objects.filter(owner=request.user)
    return JSONResponse.serialize(list(objs), aas='objects', status=200, public=False)


@csrf_exempt
def user_rating(request):
    if not request.user.is_authenticated():
        return GameError('1')

    offset = request.GET.get('offset', 0)
    order_by = ORDER_BY.get(request.GET.get('param', 'exp'), ORDER_BY['exp'])

    if order_by is None:
        order_by = 'cash'

    users = User.objects.all().order_by("-" + order_by)[offset:offset + 20]
    return JSONResponse.serialize(users, aas='users', status=200,
                                  user={'name': request.user.name, order_by: getattr(request.user, order_by),
                                        'pos': 2342352353452345234})


@csrf_exempt
def auth_vk(request):
    try:
        code = request.GET['code']
    except (KeyError, ValueError, TypeError):
        return GameError('1')

    url = \
        "https://oauth.vk.com/access_token?" + \
        "client_id=%s&" % VK_APP_ID + \
        "client_secret=%s&" % VK_APP_KEY + \
        "code=%s&" % code + \
        "redirect_uri=%s" % SettingsLocal.AUTH_REDIRECT_URL

    try:
        conn = urllib.request.urlopen(url)
        data = json.loads(conn.read().decode('utf_8'))
    except Exception as e:  # TODO: Too wide exception
        logger.error(e)
        return GameError('10')

    if 'access_token' not in data or 'user_id' not in data:
        return GameError('10')

    try:
        vk_user_id = int(data['user_id'])
    except (KeyError, ValueError, TypeError):
        return GameError('10')

    user = User.objects.create_and_auth_vk(request, vk_user_id)
    return JSONResponse.serialize(user, aas='user', status=200)


@csrf_exempt
def auth_logout(request):
    logout(request)
    return JSONResponse.serialize(status=200)


def test(request):
    return HttpResponse(render_to_string("test.html", {}))
