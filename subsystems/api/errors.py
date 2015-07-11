import json
from django.http import HttpResponse

ERRORS = {
    '1': {'status': 401, 'message': 'unauthorized access'},
    '2': {'status': 101, 'message': 'not enough args: lat and lng'},
    '3': {'status': 301, 'message': 'cant find zone at this coordinates'},
    '4': {'status': 302, 'message': 'internal foursquare error'},
    '5': {'status': 101, 'message': 'not enough args: action'},
    '6': {'status': 101, 'message': 'building id isnt specified'},
    '7': {'status': 302, 'message': 'no such building'},
    '8': {'status': 103, 'message': 'Smth wrong'},
    '9': {'status': 104, 'message': 'Invalid param specified.'},
    '10': {'status': 105, 'message': '[VK] HTTP Error 401: Unauthorized'},
    '11': {'status': 201, 'message': 'No money for action'},
    '12': {'status': 202, 'message': 'The building has owner already'},
    '13': {'status': 203, 'message': 'U have this building already'},
    '14': {'status': 203, 'message': 'U dont have this building yet'},
}


class NoMoneyError(Exception):
    pass


class HasOwnerAlready(Exception):
    pass


class UHaveIt(Exception):
    pass


class UDontHaveIt(Exception):
    pass


class GameError(HttpResponse):
    def __init__(self, code):
        super(GameError, self).__init__(json.dumps(ERRORS[code]), content_type='application/json')

