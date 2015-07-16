import json
import datetime
from django.db.models import QuerySet
from django.http import HttpResponse
from conf import secret
from subsystems.api.errors import NoMoneyError, HasOwnerAlready, UHaveIt, UDontHaveIt, SystemGameError, InDeal
from subsystems.db.model_deal import Deal
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone
from subsystems.foursquare.api import Foursquare
from conf.settings_game import DEFAULT_CATEGORIES, DUTY
from subsystems.foursquare.utils.foursquare_api import ServerError


def get_params(request, *args):
    params = []
    for arg in args:
        try:
            params.append(request.GET[arg])
        except KeyError:
            raise SystemGameError(message=arg)
    return params


def post_params(request, *args):
    params = []
    for arg in args:
        try:
            params.append(request.POST[arg])
        except KeyError:
            raise SystemGameError(message=arg)
    return params


class JSONResponse:
    @staticmethod
    def serialize(o=None, **kwargs):
        is_public = kwargs.pop('public', True)
        aas = kwargs.pop('aas', None)
        user = kwargs.pop('user_owner', None)
        if o is None:
            d = {}
        elif isinstance(o, dict):
            d = o.copy()
            d = {aas: d} if aas else d
            d.update(kwargs)
        elif isinstance(o, list) or isinstance(o, QuerySet):
            d = {aas: []}
            for obj in o:
                d[aas].append(obj.serialize(is_public, user_owner=user))
                d.update(kwargs)
        else:
            d = o.serialize(is_public)
            d = {aas: d}
        d.update(kwargs)
        return HttpResponse(json.dumps(d, ensure_ascii=False))


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
            raise NoMoneyError

        if self.venue.owner == user:
            raise UHaveIt

        if self.venue.owner:
            raise HasOwnerAlready

        self.venue.owner = user
        user.cash -= self.venue.npc_buy_price
        user.score += self.venue.expense
        user.buildings_count += 1
        user.save()
        self.venue.save()

    def sell(self, user):
        if self.venue.owner != user:
            raise UDontHaveIt

        if Deal.objects.get(venue=self.venue):
            raise InDeal
        self.venue.owner = None
        user.cash += self.venue.npc_sell_price
        user.score -= self.venue.expense if user.score >= self.venue.expense else 0
        user.buildings_count -= 1 if user.buildings_count > 0 else 0
        user.save()
        self.venue.save()

    def upgrade(self, user):
        if self.venue.owner != user:
            raise UDontHaveIt

        if user.cash < self.venue.upgrade_price:
            raise NoMoneyError

        user.cash -= self.venue.upgrade_price
        user.score += self.venue.upgrade_price
        user.save()
        self.venue.save()
