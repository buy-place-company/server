import json
import logging
import urllib.request

from django.views.decorators.csrf import csrf_exempt

from subsystems._auth import logout
from subsystems.api.errors import GameError, NoMoneyError, HasOwnerAlready, UHaveIt, UDontHaveIt, SystemGameError
from subsystems.api.utils import JSONResponse, VenueView, get_params, post_params
from subsystems.db.model_deal import Deal
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
        lat, lng = get_params(request, 'lat', 'lng')
    except SystemGameError as e:
        return GameError('no_args', e.message)
    try:
        lat = float(lat)
        lng = float(lng)
    except TypeError:
        return GameError('wrong_args', 'check: lat and lng')

    try:
        lat_size = min(request.GET.get("lat_size", ZONE_LAT_STEP), 10*ZONE_LAT_STEP)
        lng_size = min(request.GET.get("lng_size", ZONE_LNG_STEP), 10*ZONE_LNG_STEP)
    except (ValueError, TypeError):
        return GameError('wrong_args', 'check: lat_size and lng_size')

    venues = []
    for z in Zone.objects.get_zones(lat, lng, lat_size, lng_size):
        venues.extend(FoursquareAPI.get_venues_from_zone(z))

    return JSONResponse.serialize(venues, aas='venues', status=200)


@csrf_exempt
def venue_info(request):
    try:
        venue_id = get_params(request, 'venue_id')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    try:
        venue = Venue.objects.get(venue_id=venue_id)
    except Venue.DoesNotExist:
        return GameError('no_venue')

    if venue is None:
        return GameError('no_venue')

    return JSONResponse.serialize(venue, aas='objects', status=200)


@csrf_exempt
def venue_action(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

    try:
        action, venue_id = post_params(request, 'action', 'venue_id')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    if not action or not hasattr(VenueView, action):
        return GameError('no_action')

    try:
        venue = VenueView(venue_id)
    except Venue.DoesNotExists:
        return GameError('no_venue')

    try:
        getattr(venue, action)(request.user)
    except NoMoneyError:
        return GameError('no_money')
    except HasOwnerAlready:
        return GameError('owner_exists')
    except UHaveIt:
        return GameError('already_have')
    except UDontHaveIt:
        return GameError('dont_have')

    return JSONResponse.serialize(request.user, aas='user', status=200, public=False)


@csrf_exempt
def user_profile(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

    return JSONResponse.serialize(request.user, aas='user', status=200, public=False)


@csrf_exempt
def user_venues(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

    objs = Venue.objects.filter(owner=request.user)
    return JSONResponse.serialize(list(objs), aas='objects', status=200, public=False)


@csrf_exempt
def user_rating(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

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
        return GameError('no_auth')

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
        return GameError('VK', str(e))

    if 'access_token' not in data or 'user_id' not in data:
        return GameError('VK_no_auth')

    try:
        vk_user_id = int(data['user_id'])
    except (KeyError, ValueError, TypeError):
        return GameError('VK_no_auth')

    user = User.objects.create_and_auth_vk(request, vk_user_id)
    return JSONResponse.serialize(user, aas='user', status=200)


@csrf_exempt
def auth_logout(request):
    logout(request)
    return JSONResponse.serialize(status=200)


@csrf_exempt
def user_deals(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

    deals_out = [x.serialize() for x in Deal.objects.filter(user_from=request.user)]
    deals_in = [x.serialize() for x in Deal.objects.filter(user_to=request.user)]

    d = {
        'outgoing': deals_out,
        'incoming': deals_in,
    }

    return JSONResponse.serialize(o=d, aas='deals', status=200)


@csrf_exempt
def deals_new(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

    try:
        venue_id, amount = get_params(request, 'venue_id', 'amount')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    try:
        Deal.objects.get(venue=venue_id, user_from=request.user)
    except Deal.DoesNotExist:
        pass
    else:
        return JSONResponse.serialize(status=101)

    venue = Venue.objects.get(venue_id=venue_id)
    Deal.objects.create(venue=venue, user_from=request.user, user_to=venue.owner, amount=amount)
    return JSONResponse.serialize(status=200)


def test(request):
    return JSONResponse.serialize(status=200)
