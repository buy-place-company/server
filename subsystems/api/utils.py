import json
import datetime
from django.db.models import QuerySet
from django.http import HttpResponse
from conf import secret
from subsystems.api.errors import NoMoneyError, HasOwnerAlready, UHaveIt, UDontHaveIt
from subsystems.db.model_venue import Venue
from subsystems.db.model_zone import Zone
from subsystems.foursquare.api import Foursquare
from conf.settings_game import DEFAULT_CATEGORIES, DUTY
from subsystems.foursquare.utils.foursquare_api import ServerError


class JSONResponse:
    @staticmethod
    def serialize(o, **kwargs):
        is_public = kwargs.pop('public', True)
        aas = kwargs.pop('aas', 'data')
        if isinstance(o, dict):
            d = o.copy()
            d = {aas: d}
            d.update(kwargs)
            return HttpResponse(json.dumps(d, ensure_ascii=False))
        if isinstance(o, list) or isinstance(o, QuerySet):
            d = {aas: []}
            for obj in o:
                d[aas].append(obj.serialize(is_public))
                d.update(kwargs)
            a = json.dumps(d, ensure_ascii=False)
        else:
            d = o.serialize(is_public)
            d = {aas: d}
            d.update(kwargs)
            a = json.dumps(d, ensure_ascii=False)
        return HttpResponse(a)


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
