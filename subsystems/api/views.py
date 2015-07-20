import json
import logging
import urllib.request

from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now

from subsystems._auth import logout
from subsystems.api.errors import GameError, NoMoneyError, HasOwnerAlready, UHaveIt, UDontHaveIt, SystemGameError, \
    InDeal, LogWarning
from subsystems.api.utils import JSONResponse, VenueView, get_params, post_params
from subsystems.db.model_deal import Deal, STATES
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
        print(FoursquareAPI.get_venues_from_zone(z))
        venues.extend(FoursquareAPI.get_venues_from_zone(z))

    return JSONResponse.serialize(venues, user_owner=request.user, aas='venues', status=200)


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

    return JSONResponse.serialize(venue, aas='venue', status=200)


@csrf_exempt
def venue_action(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

    try:
        action, venue_id = post_params(request, 'action', 'venue_id')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    if not hasattr(VenueView, action):
        return GameError('wrong_args', 'action')

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
    except InDeal:
        return GameError('in_deal')

    res = {
        'user': request.user.serialize(False),
        'venue': venue.venue.serialize(False),
    }

    return JSONResponse.serialize(res, status=200, public=False, user_owner=request.user)


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
    return JSONResponse.serialize(list(objs), aas='venues', status=200, public=False)


@csrf_exempt
def user_rating(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

    offset = request.GET.get('offset', 0)
    order_by = ORDER_BY.get(request.GET.get('param', 'score'), ORDER_BY['score'])

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
    return JSONResponse.serialize({'id': user.id, 'name': user.name}, status=200)


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
def deal_info(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

    try:
        deal_id = get_params(request, 'deal_id')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    try:
        deal = Deal.objects.get(pk=deal_id)
    except Deal.DoesNotExist:
        return GameError('no_deal')

    if request.user == deal.user_from or request.user == deal.user_to or deal.is_public:
        return JSONResponse.serialize(deal, aas='deal', status=200)
    else:
        return GameError('no_deal')


@csrf_exempt
def deal_new(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

    try:
        venue_id, amount = get_params(request, 'venue_id', 'amount')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    venue = Venue.objects.get(venue_id=venue_id)
    if venue.owner == request.user:
        return GameError('already_have')
    elif not venue.owner:
        return GameError('no_owner')

    try:
        deal = Deal.objects.get(venue=venue_id, user_from=request.user)
    except Deal.DoesNotExist:
        pass
    else:
        return JSONResponse.serialize(deal, aas='deal', status=204)

    deal = Deal.objects.create(venue=venue, user_from=request.user, user_to=venue.owner, amount=amount)
    return JSONResponse.serialize(deal, aas='deal', status=200, user_owner=request.user)


@csrf_exempt
def deal_cancel(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

    try:
        deal_id = get_params(request, 'deal_id')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    try:
        deal = Deal.objects.get(venue=deal_id, user_from=request.user)
    except Deal.DoesNotExist:
        return GameError('no_deal')

    if request.user == deal.user_from:
        deal.state = STATES[3]
    elif request.user == deal.user_to:
        deal.state = STATES[2]
    elif not deal.is_public:
        return GameError('no_deal')
    else:
        return GameError('no_perm')
    deal.date_expire = now()
    deal.save(update_fields=['date_expire', 'state'])
    return JSONResponse.serialize(deal, aas='deal', status=200, user_owner=request.user)


@csrf_exempt
def deal_accept(request):
    if not request.user.is_authenticated():
        return GameError('no_auth')

    try:
        deal_id = get_params(request, 'venue_id', 'amount')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    try:
        deal = Deal.objects.get(venue=deal_id, user_from=request.user)
    except Deal.DoesNotExist:
        return GameError('no_deal')

    if deal.is_public or request.user == deal.user_to:
        if request.user.cash < deal.amount:
            return GameError('no_money')
        elif not deal.venue.owner:
            logger.warning(LogWarning('dont_have'))
            return GameError('dont_have')
        elif deal.venue.owner != deal.user_from:
            logger.warning(LogWarning('sold'))
            return GameError('sold')
        elif deal.venue.owner == deal.user_to:
            logger.warning(LogWarning('already_have'))
            return GameError('already_have')

        deal.user_to = request.user
        deal.user_to.cash -= deal.amount
        deal.user_to.score += deal.venue.expense
        deal.user_to.buildings_count += 1
        deal.user_from.cash += deal.venue.expense
        deal.user_from.score -= deal.venue.expense if deal.user_from.score >= deal.venue.expense else 0
        deal.user_from.buildings_count -= 1 if deal.user_from.buildings_count > 0 else 0
        deal.venue.save()
        deal.user_to.save()
        deal.user_from.save()
        deal.state = STATES[2]

    elif not deal.is_public:
        return GameError('no_deal')
    else:
        return GameError('no_perm')

    deal.state = STATES[1]
    deal.date_expire = now()
    return JSONResponse.serialize(deal, aas='deal', status=200, user_owner=request.user)

def test(request):
    return JSONResponse.serialize(status=200)
