# -*- coding: utf-8 -*-
import json
from django.http import HttpResponse

ERRORS = {
    # System errors
    'no_action': {'status': 101, 'message': '[SYS] No such action'},
    'no_venue': {'status': 302, 'message': '[SYS] No such venue'},
    'no_auth': {'status': 401, 'message': '[SYS] Unauthorized access'},
    'no_args': {'status': 101, 'message': '[SYS] Not enough args: %s'},
    'wrong_args': {'status': 101, 'message': '[SYS] Wrong args: %s'},

    # Partners errors
    'VK_no_auth': {'status': 105, 'message': '[VK] HTTP Error 401: Unauthorized'},
    'VK': {'status': 105, 'message': '[VK] %s'},

    # Game errors
    'no_money': {'status': 201, 'message': '[GAME] No money for this action'},
    'owner_exists': {'status': 202, 'message': '[GAME] The building has owner already'},
    'already_have': {'status': 203, 'message': '[GAME] U have this building already'},
    'dont_have': {'status': 203, 'message': '[GAME] U dont have this building yet'},
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
    def __init__(self, code, message_params=None):
        error = ERRORS[code].copy()
        error['message'] = (error['message'] % message_params) if message_params else error['message']
        super(GameError, self).__init__(json.dumps(error), content_type='application/json')


class SystemGameError(BaseException):
    def __init__(self, message):
        self.message = message
        super(SystemGameError, self).__init__()