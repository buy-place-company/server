import json
import datetime

from django.db.models import QuerySet
from django.http import HttpResponse
import math

from conf import secret
from conf.settings import AVATAR_DIR
from subsystems.api.errors import NoMoneyError, HasOwnerAlready, UHaveIt, UDontHaveIt, SystemGameError, \
    MaxBuildingsCountReached
from subsystems.db.model_bookmark import Bookmark
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone
from subsystems.foursquare.api import Foursquare
from conf.settings_game import DEFAULT_CATEGORIES
from subsystems.foursquare.utils.foursquare_api import ServerError
import pydenticon
import hashlib


def get_params_native(request, *args):
    params = []
    for arg in args:
        try:
            params.append(request.GET[arg])
        except KeyError:
            raise SystemGameError(message=arg)
    return params


def post_params_native(request, *args):
    params = []
    for arg in args:
        try:
            params.append(request.POST[arg])
        except KeyError:
            raise SystemGameError(message=arg)
    return params


def get_params(request, *args):
    try:
        return get_params_native(request, *args)
    except SystemGameError as e:
        try:
            return post_params_native(request, *args)
        except SystemGameError:
            raise e


def post_params(request, *args):
    try:
        return post_params_native(request, *args)
    except SystemGameError as e:
        try:
            return get_params_native(request, *args)
        except SystemGameError:
            raise e


class JSONResponse:
    RETURN_TYPE_HTTP_RESPONSE = 'h'
    RETURN_TYPE_JSON_STR = 's'
    RETURN_TYPE_DICT = 'd'

    @staticmethod
    def serialize(o=None, **kwargs):
        is_public = kwargs.pop('public', True)
        aas = kwargs.pop('aas', None)
        user = kwargs.pop('user_owner', None)
        return_type = kwargs.pop('return_type', JSONResponse.RETURN_TYPE_HTTP_RESPONSE)
        if o is None:
            d = {}
        elif isinstance(o, dict):
            d = o.copy()
            d = {aas: d} if aas else d
            d.update(kwargs)
        elif isinstance(o, list) or isinstance(o, QuerySet):
            d = {aas: []}
            for obj in o:
                d[aas].append(obj.serialize(is_public=is_public, user_owner=user))
                d.update(kwargs)
        else:
            d = o.serialize(is_public=is_public, user_owner=user)
            d = {aas: d}
        d.update(kwargs)

        if return_type == JSONResponse.RETURN_TYPE_DICT:
            return d

        dump = json.dumps(d, ensure_ascii=False)
        if return_type == JSONResponse.RETURN_TYPE_JSON_STR:
            return dump

        if return_type == JSONResponse.RETURN_TYPE_HTTP_RESPONSE:
            return HttpResponse(dump)

        return None

    @staticmethod
    def serialize_with_push(push_type, o=None, **kwargs):
        kwargs['return_type'] = JSONResponse.RETURN_TYPE_DICT
        resp_dict = JSONResponse.serialize(o, **kwargs)
        resp_http = HttpResponse(json.dumps(resp_dict, ensure_ascii=False))
        resp_dict.update({'push_type': push_type})
        if 'status' in resp_dict:
            resp_dict.pop('status')
        return resp_http, resp_dict

    @staticmethod
    def serialize_push(push_type, o=None, **kwargs):
        kwargs['return_type'] = JSONResponse.RETURN_TYPE_DICT
        resp_dict = JSONResponse.serialize(o, **kwargs)
        resp_dict.update({'push_type': push_type})
        if 'status' in resp_dict:
            resp_dict.pop('status')
        return resp_dict


class ZoneView:
    def __init__(self, sw_lat, sw_lng, ne_lat, ne_lng, list_id=None):
        self.list_id = list_id
        self.ne_lat = ne_lat
        self.ne_lng = ne_lng
        self.sw_lng = sw_lng
        self.sw_lat = sw_lat

        self.client = Foursquare(client_id=secret.client_id, client_secret=secret.secret_id, redirect_uri="http://yandex.ru")
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
        if user.cash < self.venue.expense:
            raise NoMoneyError()

        if user.buildings_count >= user.max_objects:
            raise MaxBuildingsCountReached()

        if self.venue.owner == user:
            raise UHaveIt()

        if self.venue.owner:
            raise HasOwnerAlready()

        self.venue.owner = user
        user.cash -= self.venue.npc_buy_price
        user.score += self.venue.expense
        user.buildings_count += 1
        user.save()
        Bookmark.objects.get_or_create(user=user, content_object=self.venue, is_autocreated=True)
        self.venue.save()

    def sell(self, user):
        if self.venue.owner != user:
            raise UDontHaveIt()

        # if Deal.objects.filter(venue=self.venue):
        #     raise InDeal
        self.venue.owner = None
        user.cash += self.venue.npc_sell_price
        user.score -= self.venue.expense if user.score >= self.venue.expense else 0
        user.buildings_count -= 1 if user.buildings_count > 0 else 0
        user.save()
        self.venue.save()

    def upgrade(self, user):
        if self.venue.owner != user:
            raise UDontHaveIt()

        if user.cash < self.venue.upgrade_price:
            raise NoMoneyError()

        user.cash -= self.venue.upgrade_price
        user.score += self.venue.upgrade_price
        user.save()
        self.venue.lvl += 1
        self.venue.save()

    def collect_loot(self, user):
        if self.venue.owner != user:
            raise UDontHaveIt()

        self.venue.update()
        user.cash += self.venue.loot
        self.venue.loot = 0
        user.save()
        self.venue.save()


class GPSUtils(object):
    def __init__(self, **kwargs):
        lat = kwargs['lat']
        lng = kwargs['lng']

        w = kwargs['w']
        h = kwargs['h']

        y = lat * 110.574
        x = lng * 111.320 * math.cos(lat)

        self.x1 = x - w/2
        self.y1 = y - h/2
        self.x2 = x + w/2
        self.y2 = y + h/2

    def has_point(self, lat, lng):
        y = lat * 110.574
        x = lng * 111.320 * math.cos(lat)

        if x < self.x1 or x > self.x2:
            return False
        if y < self.y1 or y > self.y2:
            return False
        return True


class AvatarUtils(object):
    foreground = [
        "rgb(45,79,255)",
        "rgb(254,180,44)",
        "rgb(226,121,234)",
        "rgb(30,179,253)",
        "rgb(232,77,65)",
        "rgb(49,203,115)",
        "rgb(141,69,170)"
    ]

    background = "rgb(224,224,224)"

    generator = pydenticon.Generator(5, 5, digest=hashlib.sha1,
                                     foreground=foreground, background=background)

    @classmethod
    def generate(cls, user):
        file_name = '%s/%d.png' % (AVATAR_DIR, user.id)
        binary_image = cls.generator.generate(file_name, 128, 128)
        f = open(file_name, 'bw')
        f.write(binary_image)
        f.close()