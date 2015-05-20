#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# (c) 2014 Mike Lewis
import logging
import pdb

log = logging.getLogger(__name__)

# Try to load JSON libraries in this order:
# ujson -> simplejson -> json
try:
    import ujson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json

import inspect
import math
import time
import sys

# 3rd party libraries that might not be present during initial install
# but we need to import for the version #
import requests

from six.moves.urllib import parse
from six.moves import xrange
import six

# Monkey patch to requests' json using ujson when available;
# Otherwise it wouldn't affect anything
requests.models.json = json


# Helpful for debugging what goes in and out
NETWORK_DEBUG = False
if NETWORK_DEBUG:
    # These two lines enable debugging at httplib level (requests->urllib3->httplib)
    # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
    import httplib

    httplib.HTTPConnection.debuglevel = 1
    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


# Default API version. Move this forward as the library is maintained and kept current
API_VERSION_YEAR = '2015'
API_VERSION_MONTH = '04'
API_VERSION_DAY = '07'
API_VERSION = '{year}{month}{day}'.format(year=API_VERSION_YEAR, month=API_VERSION_MONTH, day=API_VERSION_DAY)

# Library versioning matches supported foursquare API version
__version__ = '1!{year}.{month}.{day}'.format(year=API_VERSION_YEAR, month=API_VERSION_MONTH, day=API_VERSION_DAY)
__author__ = u'Mike Lewis'

AUTH_ENDPOINT = 'https://foursquare.com/oauth2/authenticate'
TOKEN_ENDPOINT = 'https://foursquare.com/oauth2/access_token'
API_ENDPOINT = 'https://api.foursquare.com/v2'

# Number of times to retry http requests
NUM_REQUEST_RETRIES = 3

# Max number of sub-requests per multi request
MAX_MULTI_REQUESTS = 5

# Change this if your Python distribution has issues with Foursquare's SSL cert
VERIFY_SSL = True


# Generic foursquare exception
class FoursquareException(Exception):
    pass


# Specific exceptions
class InvalidAuth(FoursquareException):
    pass


class ParamError(FoursquareException):
    pass


class EndpointError(FoursquareException):
    pass


class NotAuthorized(FoursquareException):
    pass


class RateLimitExceeded(FoursquareException):
    pass


class Deprecated(FoursquareException):
    pass


class ServerError(FoursquareException):
    pass


class FailedGeocode(FoursquareException):
    pass


class GeocodeTooBig(FoursquareException):
    pass


class Other(FoursquareException):
    pass


error_types = {
    'invalid_auth': InvalidAuth,
    'param_error': ParamError,
    'endpoint_error': EndpointError,
    'not_authorized': NotAuthorized,
    'rate_limit_exceeded': RateLimitExceeded,
    'deprecated': Deprecated,
    'server_error': ServerError,
    'failed_geocode': FailedGeocode,
    'geocode_too_big': GeocodeTooBig,
    'other': Other,
}


class Foursquare(object):
    """foursquare V2 API wrapper"""

    def __init__(self, client_id=None, client_secret=None, access_token=None, redirect_uri=None, version=None,
                 lang=None):
        """Sets up the api object"""
        # Set up OAuth
        self.oauth = self.OAuth(client_id, client_secret, redirect_uri)
        # Set up endpoints
        self.base_requester = self.Requester(client_id, client_secret, access_token, version, lang)
        # Dynamically enable endpoints
        self._attach_endpoints()

    def _attach_endpoints(self):
        """Dynamically attach endpoint callables to this client"""
        for name, endpoint in inspect.getmembers(self):
            if inspect.isclass(endpoint) and issubclass(endpoint, self._Endpoint) and (endpoint is not self._Endpoint):
                endpoint_instance = endpoint(self.base_requester)
                setattr(self, endpoint_instance.endpoint, endpoint_instance)

    def set_access_token(self, access_token):
        """Update the access token to use"""
        self.base_requester.set_token(access_token)

    @property
    def rate_limit(self):
        """Returns the maximum rate limit for the last API call i.e. X-RateLimit-Limit"""
        return self.base_requester.rate_limit

    @property
    def rate_remaining(self):
        """Returns the remaining rate limit for the last API call i.e. X-RateLimit-Remaining"""
        return self.base_requester.rate_remaining

    class OAuth(object):
        """Handles OAuth authentication procedures and helps retrieve tokens"""

        def __init__(self, client_id, client_secret, redirect_uri):
            self.client_id = client_id
            self.client_secret = client_secret
            self.redirect_uri = redirect_uri

        def auth_url(self):
            """Gets the url a user needs to access to give up a user token"""
            params = {
                'client_id': self.client_id,
                'response_type': u'code',
                'redirect_uri': self.redirect_uri,
            }
            return '{AUTH_ENDPOINT}?{params}'.format(
                AUTH_ENDPOINT=AUTH_ENDPOINT,
                params=parse.urlencode(params))

        def get_token(self, code):
            """Gets the auth token from a user's response"""
            if not code:
                log.error(u'Code not provided')
                return None
            params = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': u'authorization_code',
                'redirect_uri': self.redirect_uri,
                'code': six.u(code),
            }
            # Get the response from the token uri and attempt to parse
            return _get(TOKEN_ENDPOINT, params=params)['data']['access_token']

    # noinspection PyAttributeOutsideInit
    class Requester(object):
        """Api requesting object"""

        def __init__(self, client_id=None, client_secret=None, access_token=None, version=None, lang=None):
            """Sets up the api object"""
            self.client_id = client_id
            self.client_secret = client_secret
            self.set_token(access_token)
            self.version = version if version else API_VERSION
            self.lang = lang
            self.multi_requests = list()
            self.rate_limit = None
            self.rate_remaining = None

        def set_token(self, access_token):
            """Set the OAuth token for this requester"""
            self.oauth_token = access_token
            self.userless = not bool(access_token)  # Userless if no access_token

        def GET(self, path, params=None, **kwargs):
            """GET request that returns processed data"""
            if not params:
                params = {}
            params = params.copy()
            # Short-circuit multi requests
            if kwargs.get('multi') is True:
                return self.add_multi_request(path, params)
            # Continue processing normal requests
            headers = self._create_headers()
            params = self._enrich_params(params)
            url = '{API_ENDPOINT}{path}'.format(
                API_ENDPOINT=API_ENDPOINT,
                path=path
            )
            result = _get(url, headers=headers, params=params)
            self.rate_limit = result['headers']['X-RateLimit-Limit']
            self.rate_remaining = result['headers']['X-RateLimit-Remaining']
            return result['data']['response']

        def add_multi_request(self, path, params=None):
            """Add multi request to list and return the number of requests added"""
            if not params:
                params = {}
            url = path
            if params:
                # First convert the params into a query string then quote the whole string
                # so it will fit into the multi request query -as a value for the requests= query param-
                url += '?{0}'.format(parse.quote_plus(parse.urlencode(params)))
            self.multi_requests.append(url)
            return len(self.multi_requests)

        def POST(self, path, data=None, files=None):
            """POST request that returns processed data"""
            if not data:
                data = {}
            if data is not None:
                data = data.copy()
            if files is not None:
                files = files.copy()
            headers = self._create_headers()
            data = self._enrich_params(data)
            url = '{API_ENDPOINT}{path}'.format(
                API_ENDPOINT=API_ENDPOINT,
                path=path
            )
            result = _post(url, headers=headers, data=data, files=files)
            self.rate_limit = result['headers']['X-RateLimit-Limit']
            self.rate_remaining = result['headers']['X-RateLimit-Remaining']
            return result['data']['response']

        def _enrich_params(self, params):
            """Enrich the params dict"""
            if self.version:
                params['v'] = self.version
            if self.userless:
                params['client_id'] = self.client_id
                params['client_secret'] = self.client_secret
            else:
                params['oauth_token'] = self.oauth_token
            return params

        def _create_headers(self):
            """Get the headers we need"""
            headers = {}
            # If we specified a specific language, use that
            if self.lang:
                headers['Accept-Language'] = self.lang
            return headers

    class _Endpoint(object):
        """Generic endpoint class"""

        def __init__(self, requester):
            """Stores the request function for retrieving data"""
            self.requester = requester

        def _expanded_path(self, path=None):
            """Gets the expanded path, given this endpoint"""
            return '/{expanded_path}'.format(
                expanded_path='/'.join(p for p in (self.endpoint, path) if p)
            )

        def GET(self, path=None, *args, **kwargs):
            """Use the requester to get the data"""
            return self.requester.GET(self._expanded_path(path), *args, **kwargs)

        def POST(self, path=None, *args, **kwargs):
            """Use the requester to post the data"""
            return self.requester.POST(self._expanded_path(path), *args, **kwargs)

    class Users(_Endpoint):
        """User specific endpoint"""
        endpoint = 'users'

        def __call__(self, user_id=u'self', multi=False):
            """https://developer.foursquare.com/docs/users/users"""
            return self.GET('{user_id}'.format(user_id=user_id), multi=multi)

        """
        General
        """

        def leaderboard(self, params=None, multi=False):
            """https://developer.foursquare.com/docs/users/leaderboard"""
            if not params:
                params = {}
            return self.GET('leaderboard', params, multi=multi)

        def requests(self, multi=False):
            """https://developer.foursquare.com/docs/users/requests"""
            return self.GET('requests', multi=multi)

        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/users/search"""
            return self.GET('search', params, multi=multi)

        """
        Aspects
        """

        def badges(self, user_id=u'self', multi=False):
            """https://developer.foursquare.com/docs/users/badges"""
            return self.GET('{user_id}/badges'.format(user_id=user_id), multi=multi)

        def checkins(self, user_id=u'self', params=None, multi=False):
            """https://developer.foursquare.com/docs/users/checkins"""
            if not params:
                params = {}
            return self.GET('{user_id}/checkins'.format(user_id=user_id), params, multi=multi)

        def all_checkins(self, user_id=u'self'):
            """Utility function: Get every checkin this user has ever made"""
            offset = 0
            while True:
                checkins = self.checkins(user_id=user_id, params={'limit': 250, 'offset': offset})
                # Yield out each checkin
                for checkin in checkins['checkins']['items']:
                    yield checkin
                # Determine if we should stop here or query again
                offset += len(checkins['checkins']['items'])
                if (offset >= checkins['checkins']['count']) or (len(checkins['checkins']['items']) == 0):
                    # Break once we've processed everything
                    break

        def friends(self, user_id=u'self', params=None, multi=False):
            """https://developer.foursquare.com/docs/users/friends"""
            if not params:
                params = {}
            return self.GET('{user_id}/friends'.format(user_id=user_id), params, multi=multi)

        def lists(self, user_id=u'self', params=None, multi=False):
            """https://developer.foursquare.com/docs/users/lists"""
            if not params:
                params = {}
            return self.GET('{user_id}/lists'.format(user_id=user_id), params, multi=multi)

        def mayorships(self, user_id=u'self', params=None, multi=False):
            """https://developer.foursquare.com/docs/users/mayorships"""
            if not params:
                params = {}
            return self.GET('{user_id}/mayorships'.format(user_id=user_id), params, multi=multi)

        def photos(self, user_id=u'self', params=None, multi=False):
            """https://developer.foursquare.com/docs/users/photos"""
            if not params:
                params = {}
            return self.GET('{user_id}/photos'.format(user_id=user_id), params, multi=multi)

        def tips(self, user_id=u'self', params=None, multi=False):
            """https://developer.foursquare.com/docs/users/tips"""
            if not params:
                params = {}
            return self.GET('{user_id}/tips'.format(user_id=user_id), params, multi=multi)

        def todos(self, user_id=u'self', params=None, multi=False):
            """https://developer.foursquare.com/docs/users/todos"""
            if not params:
                params = {}
            return self.GET('{user_id}/todos'.format(user_id=user_id), params, multi=multi)

        def venuehistory(self, user_id=u'self', params=None, multi=False):
            """https://developer.foursquare.com/docs/users/venuehistory"""
            if not params:
                params = {}
            return self.GET('{user_id}/venuehistory'.format(user_id=user_id), params, multi=multi)

        def venuelikes(self, user_id=u'self', params=None, multi=False):
            """https://developer.foursquare.com/docs/users/venuelikes"""
            if not params:
                params = {}
            return self.GET('{user_id}/venuelikes'.format(user_id=user_id), params, multi=multi)

        """
        Actions
        """

        def approve(self, user_id):
            """https://developer.foursquare.com/docs/users/approve"""
            return self.POST('{user_id}/approve'.format(user_id=user_id))

        def deny(self, user_id):
            """https://developer.foursquare.com/docs/users/deny"""
            return self.POST('{user_id}/deny'.format(user_id=user_id))

        def request(self, user_id):
            """https://developer.foursquare.com/docs/users/request"""
            return self.POST('{user_id}/request'.format(user_id=user_id))

        def setpings(self, user_id, params):
            """https://developer.foursquare.com/docs/users/setpings"""
            return self.POST('{user_id}/setpings'.format(user_id=user_id), params)

        def unfriend(self, user_id):
            """https://developer.foursquare.com/docs/users/unfriend"""
            return self.POST('{user_id}/unfriend'.format(user_id=user_id))

        def update(self, params=None, photo_data=None, photo_content_type='image/jpeg'):
            """https://developer.foursquare.com/docs/users/update"""
            if not params:
                params = {}
            if photo_data:
                files = {'photo': ('photo', photo_data, photo_content_type)}
            else:
                files = None
            return self.POST('self/update', data=params, files=files)

    class Venues(_Endpoint):
        """Venue specific endpoint"""
        endpoint = 'venues'

        """
        General
        """

        def __call__(self, venue_id, multi=False):
            """https://developer.foursquare.com/docs/venues/venues"""
            return self.GET('{venue_id}'.format(venue_id=venue_id), multi=multi)

        def add(self, params):
            """https://developer.foursquare.com/docs/venues/add"""
            return self.POST('add', params)

        def categories(self, params=None, multi=False):
            """https://developer.foursquare.com/docs/venues/categories"""
            if not params:
                params = {}
            return self.GET('categories', params, multi=multi)

        def explore(self, params, multi=False):
            """https://developer.foursquare.com/docs/venues/explore"""
            return self.GET('explore', params, multi=multi)

        def managed(self, multi=False):
            """https://developer.foursquare.com/docs/venues/managed"""
            return self.GET('managed', multi=multi)

        MAX_SEARCH_LIMIT = 50

        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/venues/search"""
            return self.GET('search', params, multi=multi)

        def suggestcompletion(self, params, multi=False):
            """https://developer.foursquare.com/docs/venues/suggestcompletion"""
            return self.GET('suggestcompletion', params, multi=multi)

        def trending(self, params, multi=False):
            """https://developer.foursquare.com/docs/venues/trending"""
            return self.GET('trending', params, multi=multi)

        """
        Aspects
        """

        def events(self, venue_id, multi=False):
            """https://developer.foursquare.com/docs/venues/events"""
            return self.GET('{venue_id}/events'.format(venue_id=venue_id), multi=multi)

        def herenow(self, venue_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/venues/herenow"""
            if not params:
                params = {}
            return self.GET('{venue_id}/herenow'.format(venue_id=venue_id), params, multi=multi)

        def links(self, venue_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/venues/links"""
            if not params:
                params = {}
            return self.GET('{venue_id}/links'.format(venue_id=venue_id), params, multi=multi)

        def listed(self, venue_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/venues/listed"""
            if not params:
                params = {}
            return self.GET('{venue_id}/listed'.format(venue_id=venue_id), params, multi=multi)

        def menu(self, venue_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/venues/menu"""
            if not params:
                params = {}
            return self.GET('{venue_id}/menu'.format(venue_id=venue_id), params, multi=multi)

        def photos(self, venue_id, params, multi=False):
            """https://developer.foursquare.com/docs/venues/photos"""
            return self.GET('{venue_id}/photos'.format(venue_id=venue_id), params, multi=multi)

        def similar(self, venue_id, multi=False):
            """https://developer.foursquare.com/docs/venues/similar"""
            return self.GET('{venue_id}/similar'.format(venue_id=venue_id), multi=multi)

        def stats(self, venue_id, multi=False):
            """https://developer.foursquare.com/docs/venues/stats"""
            return self.GET('{venue_id}/stats'.format(venue_id=venue_id), multi=multi)

        def tips(self, venue_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/venues/tips"""
            if not params:
                params = {}
            return self.GET('{venue_id}/tips'.format(venue_id=venue_id), params, multi=multi)

        def nextvenues(self, venue_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/venues/nextvenues"""
            if not params:
                params = {}
            return self.GET('{venue_id}/nextvenues'.format(venue_id=venue_id), params, multi=multi)

        def likes(self, venue_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/venues/likes"""
            if not params:
                params = {}
            return self.GET('{venue_id}/likes'.format(venue_id=venue_id), params, multi=multi)

        def hours(self, venue_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/venues/hours"""
            if not params:
                params = {}
            return self.GET('{venue_id}/hours'.format(venue_id=venue_id), params, multi=multi)

        """
        Actions
        """

        def edit(self, venue_id, params=None):
            """https://developer.foursquare.com/docs/venues/edit"""
            if not params:
                params = {}
            return self.POST('{venue_id}/edit'.format(venue_id=venue_id), params)

        def flag(self, venue_id, params):
            """https://developer.foursquare.com/docs/venues/flag"""
            return self.POST('{venue_id}/flag'.format(venue_id=venue_id), params)

        def marktodo(self, venue_id, params=None):
            """https://developer.foursquare.com/docs/venues/marktodo"""
            if not params:
                params = {}
            return self.POST('{venue_id}/marktodo'.format(venue_id=venue_id), params)

        def proposeedit(self, venue_id, params):
            """https://developer.foursquare.com/docs/venues/proposeedit"""
            return self.POST('{venue_id}/proposeedit'.format(venue_id=venue_id), params)

        def setrole(self, venue_id, params):
            """https://developer.foursquare.com/docs/venues/setrole"""
            return self.POST('{venue_id}/setrole'.format(venue_id=venue_id), params)

    class Checkins(_Endpoint):
        """Checkin specific endpoint"""
        endpoint = 'checkins'

        def __call__(self, checkin_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/checkins/checkins"""
            if not params:
                params = {}
            return self.GET('{checkin_id}'.format(checkin_id=checkin_id), params, multi=multi)

        def add(self, params):
            """https://developer.foursquare.com/docs/checkins/add"""
            return self.POST('add', params)

        def recent(self, params=None, multi=False):
            """https://developer.foursquare.com/docs/checkins/recent"""
            if not params:
                params = {}
            return self.GET('recent', params, multi=multi)

        """
        Actions
        """

        def addcomment(self, checkin_id, params):
            """https://developer.foursquare.com/docs/checkins/addcomment"""
            return self.POST('{checkin_id}/addcomment'.format(checkin_id=checkin_id), params)

        def addpost(self, checkin_id, params):
            """https://developer.foursquare.com/docs/checkins/addpost"""
            return self.POST('{checkin_id}/addpost'.format(checkin_id=checkin_id), params)

        def deletecomment(self, checkin_id, params):
            """https://developer.foursquare.com/docs/checkins/deletecomment"""
            return self.POST('{checkin_id}/deletecomment'.format(checkin_id=checkin_id), params)

        def reply(self, checkin_id, params):
            """https://developer.foursquare.com/docs/checkins/reply"""
            return self.POST('{checkin_id}/reply'.format(checkin_id=checkin_id), params)

    class Tips(_Endpoint):
        """Tips specific endpoint"""
        endpoint = 'tips'

        def __call__(self, tip_id, multi=False):
            """https://developer.foursquare.com/docs/tips/tips"""
            return self.GET('{tip_id}'.format(tip_id=tip_id), multi=multi)

        def add(self, params):
            """https://developer.foursquare.com/docs/tips/add"""
            return self.POST('add', params)

        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/tips/add"""
            return self.GET('search', params, multi=multi)

        """
        Aspects
        """

        def done(self, tip_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/tips/done"""
            if not params:
                params = {}
            return self.GET('{tip_id}/done'.format(tip_id=tip_id), params, multi=multi)

        def listed(self, tip_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/tips/listed"""
            if not params:
                params = {}
            return self.GET('{tip_id}/listed'.format(tip_id=tip_id), params, multi=multi)

        """
        Actions
        """

        def markdone(self, tip_id):
            """https://developer.foursquare.com/docs/tips/markdone"""
            return self.POST('{tip_id}/markdone'.format(tip_id=tip_id))

        def marktodo(self, tip_id):
            """https://developer.foursquare.com/docs/tips/marktodo"""
            return self.POST('{tip_id}/marktodo'.format(tip_id=tip_id))

        def unmark(self, tip_id):
            """https://developer.foursquare.com/docs/tips/unmark"""
            return self.POST('{tip_id}/unmark'.format(tip_id=tip_id))

    class Lists(_Endpoint):
        """Lists specific endpoint"""
        endpoint = 'lists'

        def __call__(self, list_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/lists/lists"""
            if not params:
                params = {}
            return self.GET('{list_id}'.format(list_id=list_id), params, multi=multi)

        def add(self, params):
            """https://developer.foursquare.com/docs/lists/add"""
            return self.POST('add', params)

        """
        Aspects
        """

        def followers(self, list_id, multi=False):
            """https://developer.foursquare.com/docs/lists/followers"""
            return self.GET('{list_id}/followers'.format(list_id=list_id), multi=multi)

        def suggestphoto(self, list_id, params, multi=False):
            """https://developer.foursquare.com/docs/lists/suggestphoto"""
            return self.GET('{list_id}/suggestphoto'.format(list_id=list_id), params, multi=multi)

        def suggesttip(self, list_id, params, multi=False):
            """https://developer.foursquare.com/docs/lists/suggesttip"""
            return self.GET('{list_id}/suggesttip'.format(list_id=list_id), params, multi=multi)

        def suggestvenues(self, list_id, multi=False):
            """https://developer.foursquare.com/docs/lists/suggestvenues"""
            return self.GET('{list_id}/suggestvenues'.format(list_id=list_id), multi=multi)

        """
        Actions
        """

        def additem(self, list_id, params):
            """https://developer.foursquare.com/docs/lists/additem"""
            return self.POST('{list_id}/additem'.format(list_id=list_id), params)

        def deleteitem(self, list_id, params):
            """https://developer.foursquare.com/docs/lists/deleteitem"""
            return self.POST('{list_id}/deleteitem'.format(list_id=list_id), params)

        def follow(self, list_id):
            """https://developer.foursquare.com/docs/lists/follow"""
            return self.POST('{list_id}/follow'.format(list_id=list_id))

        def moveitem(self, list_id, params):
            """https://developer.foursquare.com/docs/lists/moveitem"""
            return self.POST('{list_id}/moveitem'.format(list_id=list_id), params)

        def share(self, list_id, params):
            """https://developer.foursquare.com/docs/lists/share"""
            return self.POST('{list_id}/share'.format(list_id=list_id), params)

        def unfollow(self, list_id):
            """https://developer.foursquare.com/docs/tips/unfollow"""
            return self.POST('{list_id}/unfollow'.format(list_id=list_id))

        def update(self, list_id, params):
            """https://developer.foursquare.com/docs/tips/update"""
            return self.POST('{list_id}/update'.format(list_id=list_id), params)

        def updateitem(self, list_id, params):
            """https://developer.foursquare.com/docs/tips/updateitem"""
            return self.POST('{list_id}/updateitem'.format(list_id=list_id), params)

    class Photos(_Endpoint):
        """Photo specific endpoint"""
        endpoint = 'photos'

        def __call__(self, photo_id, multi=False):
            """https://developer.foursquare.com/docs/photos/photos"""
            return self.GET('{photo_id}'.format(photo_id=photo_id), multi=multi)

        def add(self, photo_data, params, photo_content_type='image/jpeg'):
            """https://developer.foursquare.com/docs/photos/add"""
            files = {'photo': ('photo', photo_data, photo_content_type)}
            return self.POST('add', data=params, files=files)

    class Settings(_Endpoint):
        """Setting specific endpoint"""
        endpoint = 'settings'

        def __call__(self, setting_id, multi=False):
            """https://developer.foursquare.com/docs/settings/settings"""
            return self.GET('{setting_id}'.format(setting_id=setting_id), multi=multi)

        def all(self, multi=False):
            """https://developer.foursquare.com/docs/settings/all"""
            return self.GET('all', multi=multi)

        """
        Actions
        """

        def set(self, setting_id, params):
            """https://developer.foursquare.com/docs/settings/set"""
            return self.POST('{setting_id}/set'.format(setting_id=setting_id), params)

    class Specials(_Endpoint):
        """Specials specific endpoint"""
        endpoint = 'specials'

        def __call__(self, special_id, params, multi=False):
            """https://developer.foursquare.com/docs/specials/specials"""
            return self.GET('{special_id}'.format(special_id=special_id), params, multi=multi)

        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/specials/search"""
            return self.GET('search', params, multi=multi)

        """
        Actions
        """

        def add(self, special_id, params):
            """https://developer.foursquare.com/docs/specials/add"""
            return self.POST('add', params)

        def flag(self, special_id, params):
            """https://developer.foursquare.com/docs/specials/flag"""
            return self.POST('{special_id}/flag'.format(special_id=special_id), params)

    class Events(_Endpoint):
        """Events specific endpoint"""
        endpoint = 'events'

        def __call__(self, event_id, multi=False):
            """https://developer.foursquare.com/docs/events/events"""
            return self.GET('{event_id}'.format(event_id=event_id), multi=multi)

        def categories(self, multi=False):
            """https://developer.foursquare.com/docs/events/categories"""
            return self.GET('categories', multi=multi)

        def search(self, params, multi=False):
            """https://developer.foursquare.com/docs/events/search"""
            return self.GET('search', params, multi=multi)

    class Pages(_Endpoint):
        """Pages specific endpoint"""
        endpoint = 'pages'

        def __call__(self, user_id, multi=False):
            """https://developer.foursquare.com/docs/pages/pages"""
            return self.GET('{user_id}'.format(user_id=user_id), multi=multi)

        def venues(self, page_id, params=None, multi=False):
            """https://developer.foursquare.com/docs/pages/venues"""
            if not params:
                params = {}
            return self.GET('{page_id}/venues'.format(page_id=page_id), params, multi=multi)

    class Multi(_Endpoint):
        """Multi request endpoint handler"""
        endpoint = 'multi'

        def __len__(self):
            return len(self.requester.multi_requests)

        def __call__(self):
            """
            Generator to process the current queue of multi's
            note: This generator will yield both data and FoursquareException's
            The code processing this sequence must check the yields for their type.
            The exceptions should be handled by the calling code, or raised.
            """
            while self.requester.multi_requests:
                # Pull n requests from the multi-request queue
                _requests = self.requester.multi_requests[:MAX_MULTI_REQUESTS]
                del (self.requester.multi_requests[:MAX_MULTI_REQUESTS])
                # Process the 4sq multi request
                params = {
                    'requests': ','.join(_requests),
                }
                responses = self.GET(params=params)['responses']
                # ... and yield out each individual response
                for response in responses:
                    # Make sure the response was valid
                    try:
                        _raise_error_from_response(response)
                        yield response['response']
                    except FoursquareException as e:
                        yield e

        @property
        def num_required_api_calls(self):
            """Returns the expected number of API calls to process"""
            return int(math.ceil(len(self.requester.multi_requests) / float(MAX_MULTI_REQUESTS)))


def _log_and_raise_exception(msg, data, cls=FoursquareException):
    """Calls log.error() then raises an exception of class cls"""
    data = u'{0}'.format(data)
    # We put data as a argument for log.error() so error tracking systems such
    # as Sentry will properly group errors together by msg only
    log.error(u'{0}: %s'.format(msg), data)
    raise cls(u'{0}: {1}'.format(msg, data))


"""
Network helper functions
"""


def _get(url, headers=None, params=None):
    """Tries to GET data from an endpoint using retries"""
    if not headers:
        headers = {}
    param_string = _foursquare_urlencode(params)
    for i in xrange(NUM_REQUEST_RETRIES):
        try:
            try:
                response = requests.get(url, headers=headers, params=param_string, verify=VERIFY_SSL)
                pdb.set_trace()
                return _process_response(response)
            except requests.exceptions.RequestException as e:
                _log_and_raise_exception('Error connecting with foursquare API', e)
        except FoursquareException as e:
            # Some errors don't bear repeating
            if e.__class__ in [InvalidAuth, ParamError, EndpointError, NotAuthorized, Deprecated]:
                raise
            # If we've reached our last try, re-raise
            if (i + 1) == NUM_REQUEST_RETRIES:
                raise
        time.sleep(1)


def _post(url, headers=None, data=None, files=None):
    """Tries to POST data to an endpoint"""
    if not headers:
        headers = {}
    try:
        response = requests.post(url, headers=headers, data=data, files=files, verify=VERIFY_SSL)
        return _process_response(response)
    except requests.exceptions.RequestException as e:
        _log_and_raise_exception('Error connecting with foursquare API', e)


def _process_response(response):
    """Make the request and handle exception processing"""
    # Read the response as JSON
    try:
        data = response.json()
    except ValueError:
        _log_and_raise_exception('Invalid response', response.text)

    # Default case, Got proper response
    if response.status_code == 200:
        return {'headers': response.headers, 'data': data}
    return _raise_error_from_response(data)


def _raise_error_from_response(data):
    """Processes the response data"""
    # Check the meta-data for why this request failed
    meta = data.get('meta')
    if meta:
        # Account for foursquare conflicts
        # see: https://developer.foursquare.com/overview/responses
        if meta.get('code') in (200, 409):
            return data
        exc = error_types.get(meta.get('errorType'))
        if exc:
            raise exc(meta.get('errorDetail'))
        else:
            _log_and_raise_exception('Unknown error. meta', meta)
    else:
        _log_and_raise_exception('Response format invalid, missing meta property. data', data)


def _as_utf8(s):
    try:
        return str(s)
    except UnicodeEncodeError:
        return s.encode('utf8')


def _foursquare_urlencode(query, doseq=0, safe_chars="&/,+"):
    """Gnarly hack because Foursquare doesn't properly handle standard url encoding"""
    # Original doc: http://docs.python.org/2/library/urllib.html#urllib.urlencode
    # Works the same way as urllib.urlencode except two differences -
    # 1. it uses `quote()` instead of `quote_plus()`
    # 2. it takes an extra parameter called `safe_chars` which is a string
    # having the characters which should not be encoded.
    #
    # Courtesy of github.com/iambibhas
    if hasattr(query, "items"):
        # mapping objects
        query = query.items()
    else:
        # it's a bother at times that strings and string-like objects are
        # sequences...
        try:
            # non-sequence items should not work with len()
            # non-empty strings will fail this
            if len(query) and not isinstance(query[0], tuple):
                raise TypeError
                # zero-length sequences of all types will get here and succeed,
                # but that's a minor nit - since the original implementation
                # allowed empty dicts that type of behavior probably should be
                # preserved for consistency
        except TypeError:
            ty, va, tb = sys.exc_info()
            raise TypeError("not a valid non-string sequence or mapping object").with_traceback(tb)

    l = []
    if not doseq:
        # preserve old behavior
        for k, v in query:
            k = parse.quote(_as_utf8(k), safe=safe_chars)
            v = parse.quote(_as_utf8(v), safe=safe_chars)
            l.append(k + '=' + v)
    else:
        for k, v in query:
            k = parse.quote(_as_utf8(k), safe=safe_chars)
            if isinstance(v, six.string_types):
                v = parse.quote(_as_utf8(v), safe=safe_chars)
                l.append(k + '=' + v)
            else:
                try:
                    # is this a sufficient test for sequence-ness?
                    len(v)
                except TypeError:
                    # not a sequence
                    v = parse.quote(_as_utf8(v), safe=safe_chars)
                    l.append(k + '=' + v)
                else:
                    # loop over the sequence
                    for elt in v:
                        l.append(k + '=' + parse.quote(_as_utf8(elt)))
    return '&'.join(l)
