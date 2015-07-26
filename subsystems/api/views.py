import json
import logging
import urllib.request

from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from subsystems.api.decor import auth_required
from subsystems.db.model_venue import Bookmark
from subsystems.gcm.models import Device

from subsystems._auth import logout
from subsystems.api.errors import GameError, NoMoneyError, HasOwnerAlready, UHaveIt, UDontHaveIt, SystemGameError, \
    InDeal, LogWarning
from subsystems.api.utils import JSONResponse, VenueView, get_params, post_params, GPSUtils, AvatarUtils
from subsystems.db.model_deal import Deal, STATES, TYPES
from subsystems.db.model_user import User
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone
from subsystems.foursquare.api import FoursquareAPI
from conf.settings_local import SettingsLocal
from conf.secret import VK_APP_KEY, VK_APP_ID
from conf.settings_game import ORDER_BY, ZONE_LNG_STEP, ZONE_LAT_STEP, ZONE_RETURN_WIDTH, ZONE_RETURN_HEIGHT

logger = logging.getLogger(__name__)


@csrf_exempt
@auth_required
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
        lat_size = min(int(request.GET.get("lat_size", ZONE_LAT_STEP)), 2*ZONE_LAT_STEP)
        lng_size = min(int(request.GET.get("lng_size", ZONE_LNG_STEP)), 2*ZONE_LNG_STEP)
        km_width = min(int(request.GET.get("km_width", ZONE_RETURN_WIDTH)), 2*ZONE_RETURN_WIDTH)
        km_height = min(int(request.GET.get("km_width", ZONE_RETURN_HEIGHT)), 2*ZONE_RETURN_HEIGHT)
    except (ValueError, TypeError):
        return GameError('wrong_args', 'check: lat_size, lng_size, km_width, km_height')

    venues = []
    for z in Zone.objects.get_zones(lat, lng, lat_size, lng_size):
        venues.extend(FoursquareAPI.get_venues_from_zone(z))

    gpsutils = GPSUtils(lat=lat, lng=lng, w=km_width, h=km_height)

    venues_km = []
    for v in venues:
        if True or gpsutils.has_point(v.lat, v.lng):
            venues_km.append(v)

    return JSONResponse.serialize(venues_km, user_owner=request.user, aas='venues', status=200)


@csrf_exempt
@auth_required
def venue_info(request):
    try:
        venue_id, = get_params(request, 'venue_id')
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
@auth_required
def venue_action(request):
    try:
        action, venue_id = post_params(request, 'action', 'venue_id')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    if not hasattr(VenueView, action):
        return GameError('wrong_args', 'action')

    try:
        venue = VenueView(venue_id)
    except Venue.DoesNotExist:
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
        'user': request.user.serialize(user_owner=request.user),
        'venue': venue.venue.serialize(user_owner=request.user),
    }

    return JSONResponse.serialize(res, status=200, public=False, user_owner=request.user)


@csrf_exempt
@auth_required
def user_profile(request):
    return JSONResponse.serialize(request.user, aas='user', status=200, public=False)


@csrf_exempt
@auth_required
def user_venues(request):
    try:
        user_id, = get_params(request, 'user_id')
    except SystemGameError as e:
        user_id = request.user

    objs = Venue.objects.filter(owner=user_id)
    return JSONResponse.serialize(list(objs), aas='venues', status=200, user_owner=request.user)


@csrf_exempt
@auth_required
def user_rating(request):
    offset = int(request.GET.get('offset', 0))
    order_by = ORDER_BY.get(request.GET.get('param', 'score'), ORDER_BY['score'])
    limit = int(request.GET.get('limit', 20))

    if order_by is None:
        order_by = '_score'

    users = User.objects.all().order_by("-" + order_by)[offset:offset + limit]
    return JSONResponse.serialize(users, aas='users', status=200, user={'user': request.user.serialize(is_public=False)},
                                  user_owner=request.user)


@csrf_exempt
def auth_vk(request):
    try:
        code, = get_params(request, 'code')
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

    try:
        user = User.objects.get(id_vk=vk_user_id)
        user = User.objects.auth(request, user)
    except User.DoesNotExist:
        url = \
            "https://api.vk.com/method/users.get?" + \
            "user_ids=%d&" % vk_user_id + \
            "v=5.33"

        try:
            conn = urllib.request.urlopen(url)
            data = json.loads(conn.read().decode('utf_8'))['response']
            name = '{0} {1}'.format(data[0]['first_name'], data[0]['last_name'])
        except:
            name = ''

        user = User.objects.create_and_auth_vk(request, vk_user_id, name)
        AvatarUtils.generate(user)

    return JSONResponse.serialize({'id': user.id, 'name': user.name}, status=200)


@csrf_exempt
def auth_logout(request):
    try:
        logout(request)
    except:
        pass
    return JSONResponse.serialize(status=200)


@csrf_exempt
def auth_signup(request):
    try:
        email, password, name = post_params(request, 'email', 'password', 'name')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    try:
        user = User.objects.create_and_auth_email(request, email, password, name)
        AvatarUtils.generate(user)
    except:
        return GameError('user_already_exists')

    return JSONResponse.serialize({'id': user.id, 'name': user.name}, status=200)


@csrf_exempt
def auth_email(request):
    try:
        email, password = post_params(request, 'email', 'password')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    try:
        email = User.objects.normalize_email(email)
        user = User.objects.get(email=email)
        user = User.objects.auth(request, user, password=password)
        if user is None:
            return GameError('user_not_exists')
    except User.DoesNotExist:
        return GameError('user_not_exists')

    return JSONResponse.serialize({'id': user.id, 'name': user.name}, status=200)


@csrf_exempt
@auth_required
def user_deals(request):
    deals_out = [x.serialize(user_owner=request.user) for x in Deal.objects.filter(user_from=request.user)]
    deals_in = [x.serialize(user_owner=request.user) for x in Deal.objects.filter(user_to=request.user)]

    d = {
        'outgoing': deals_out,
        'incoming': deals_in,
    }

    return JSONResponse.serialize(o=d, aas='deals', status=200)


@csrf_exempt
@auth_required
def user_bookmarks(request):
    bookmarks = Bookmark.objects.filter(user=request.user)
    return JSONResponse.serialize(o=bookmarks, aas='venues', status=200)


@csrf_exempt
@auth_required
def deal_info(request):
    try:
        deal_id, = get_params(request, 'deal_id')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    try:
        deal = Deal.objects.get(id=deal_id)
    except Deal.DoesNotExist:
        return GameError('no_deal')

    if request.user == deal.user_from or request.user == deal.user_to or deal.is_public:
        return JSONResponse.serialize(deal, aas='deal', status=200, user_owner=request.user)
    else:
        return GameError('no_deal')


@csrf_exempt
@auth_required
def deal_new(request):
    if not request.user.has_place():
        return GameError('no_place')
    try:
        venue_id, amount = get_params(request, 'venue_id', 'amount')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    try:
        venue = Venue.objects.get(venue_id=venue_id)
    except Venue.DoesNotExist:
        return GameError('no_venue')
    if venue.owner == request.user:
        dtype = TYPES[1][0]
        is_pub = True
    elif not venue.owner:
        return GameError('no_owner')
    else:
        dtype = TYPES[0][0]
        is_pub = False

    deal = Deal.objects.filter(venue=venue_id, user_from=request.user, state=STATES[0][0]).exclude(dtype=[TYPES[1][0], TYPES[0][0]])
    if deal:
        deal = deal.first()
        status = 204
    else:
        deal = Deal.objects.create(venue=venue, user_from=request.user, user_to=venue.owner if not is_pub else None,
                                   amount=amount, state=STATES[0][0], dtype=dtype, is_public=is_pub)
        status = 200
        request.user.buildings_count += 1
        request.user.save()

    resp, push = JSONResponse.serialize_with_push('deal_new', deal, aas='deal', status=status, user_owner=request.user)

    if deal.user_to is not None:
        msg = Device.objects.filter(user=deal.user_to).send_message(push)
        logger.warn("Where: deal_new\n" + str(msg))

    return resp


@csrf_exempt
@auth_required
def deal_cancel(request):
    try:
        deal_id, = get_params(request, 'deal_id')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    try:
        deal = Deal.objects.get(id=deal_id)
    except Deal.DoesNotExist:
        return GameError('no_deal')

    if request.user == deal.user_from:
        deal.state = STATES[3][0]
        push_to_user = deal.user_to
        push_type = 'deal_revoke'
    elif request.user == deal.user_to:
        deal.state = STATES[2][0]
        push_to_user = deal.user_from
        push_type = 'deal_reject'
    elif not deal.is_public:
        return GameError('no_deal')
    else:
        return GameError('no_perm')

    resp, push = JSONResponse.serialize_with_push(push_type, deal, aas='deal', status=200, user_owner=request.user)

    if deal.user_to is not None:
        msg = Device.objects.filter(user=push_to_user).send_message(push)
        logger.warn("Where: deal_cancel\n" + str(msg))

    return resp


@csrf_exempt
@auth_required
def deal_accept(request):
    try:
        deal_id, = get_params(request,  'deal_id')
    except SystemGameError as e:
        return GameError('no_args', e.message)

    try:
        deal = Deal.objects.get(id=deal_id)
    except Deal.DoesNotExist:
        return GameError('no_deal')

    # if deal.state != STATES[0][0]:
    #     return JSONResponse.serialize(deal, aas='deal', status=200, user_owner=request.user)

    if deal.is_public or request.user == deal.user_to:
        if not deal.venue.owner:
            logger.warning(LogWarning('dont_have'))
            return GameError('dont_have')
        elif deal.dtype == TYPES[0][0] and deal.venue.owner != deal.user_to:
            logger.warning(LogWarning('sold'))
            return GameError('sold')
        elif deal.dtype == TYPES[1][0] and deal.venue.owner != deal.user_from:
            logger.warning(LogWarning('sold'))
            return GameError('sold')

        if deal.dtype == TYPES[0][0]:
            if deal.user_from.cash < deal.amount:
                return GameError('no_money')
            deal.user_to = request.user
            deal.user_to.cash += deal.amount
            deal.user_to.buildings_count -= 1
            deal.user_from.cash -= deal.venue.expense
            deal.user_from.buildings_count += 1
            deal.venue.owner = deal.user_from
            deal.venue.save()
            deal.user_to.save()
            deal.user_from.save()
        elif deal.dtype == TYPES[1][0]:
            if request.user.cash < deal.amount:
                return GameError('no_money')
            if not request.user.has_place():
                return GameError('no_place')
            deal.user_to = request.user
            deal.user_from.cash += deal.amount
            deal.user_from.buildings_count -= 1
            deal.user_to.cash -= deal.venue.expense
            deal.user_to.buildings_count += 1
            deal.venue.owner = deal.user_to
            deal.venue.save()
            deal.user_to.save()
            deal.user_from.save()
        deal.state = STATES[1][0]
        deal.date_expire = now()
        deal.save()
    elif not deal.is_public:
        return GameError('no_deal')
    else:
        return GameError('no_perm')

    if request.user == deal.user_from:
        push_to_user = deal.user_to
    elif request.user == deal.user_to:
        push_to_user = deal.user_from
    else:
        push_to_user = None

    resp, push = JSONResponse.serialize_with_push('deal_accept', deal, aas='deal', status=200, user_owner=request.user)

    if deal.user_to is not None:
        msg = Device.objects.filter(user=push_to_user).send_message(push)
        logger.warn("Where: deal_accept\n" + str(msg))

    return resp


@csrf_exempt
@auth_required
def bookmark_new(request):
    try:
        venue_id, = post_params(request, 'venue_id')
    except SystemGameError as e:
        return GameError('no_args', message_params=e.message)

    try:
        obj = Venue.objects.get(venue_id=venue_id)
    except Venue.DoesNotExist:
        return GameError('wrong_args', 'venue_id')
    obj = Bookmark.objects.get_or_create(user=request.user, venue=obj, is_autocreated=False)
    print(obj)
    return JSONResponse.serialize(obj, aas='venue', status=200)


@csrf_exempt
@auth_required
def bookmark_delete(request):
    try:
        venue_id, = post_params(request, 'venue_id')
    except SystemGameError as e:
        return GameError('no_args', message_params=e.message)

    try:
        venue = Venue.objects.get(venue_id=venue_id)
    except Venue.DoesNotExist:
        return GameError('no_venue')
    try:
        obj = Bookmark.objects.get(user=request.user, venue=venue)
    except Bookmark.DoesNotExist:
        return GameError('no_bookmark')
    venue = obj.venue
    obj.delete()
    return JSONResponse.serialize(venue, aas='venue', status=200)


@csrf_exempt
@auth_required
def push_reg(request):
    try:
        reg_id, = post_params(request, 'reg_id')
    except SystemGameError as e:
        return GameError('no_args', message_params=e.message)

    try:
        Device.objects.create(reg_id=reg_id, user=request.user)
    except Exception as e:
        logger.warning(e)
    return JSONResponse.serialize(status=200)


@csrf_exempt
@auth_required
def push_unreg(request):
    try:
        reg_id, = post_params(request, 'reg_id')
    except SystemGameError as e:
        return GameError('no_args', message_params=e.message)

    try:
        device = Device.objects.get(reg_id=reg_id)
        device.clear()
    except Exception as e:
        logger.warning(e)
    return JSONResponse.serialize(status=200)


@csrf_exempt
def test_image(request):
    for u in User.objects.all():
        AvatarUtils.generate(u)