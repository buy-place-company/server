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
    'no_deal': {'status': 403, 'message': '[SYS] No such deal'},
    'no_bookmark': {'status': 403, 'message': '[SYS] No such bookmark'},

    # Partners errors
    'VK_no_auth': {'status': 105, 'message': '[VK] HTTP Error 401: Unauthorized'},
    'VK': {'status': 105, 'message': '[VK] %s'},

    # auth errors
    'user_already_exists': {'status': 601, 'message': '[AUTH] User already exists'},
    'user_not_exists': {'status': 602, 'message': '[AUTH] User does not exists or password is wrong'},

    # Game errors
    'no_money': {'status': 201, 'message': '[GAME] No money for this action'},
    'owner_exists': {'status': 202, 'message': '[GAME] The building has owner already'},
    'already_have': {'status': 203, 'message': '[GAME] U have this building already'},
    'dont_have': {'status': 203, 'message': '[GAME] U dont have this building yet'},
    'no_owner': {'status': 214, 'message': '[GAME] No one doesnt have this building yet'},
    'in_deal': {'status': 215, 'message': '[GAME] Building is a part of deal already'},
    'sold': {'status': 216, 'message': '[GAME] Building has been sold already'},
    'no_place': {'status': 217, 'message': '[GAME] You have no places for building'},
    'no_place_other': {'status': 218, 'message': '[SYS] No such bookmark'},
    'no_money_other': {'status': 219, 'message': '[GAME] No money for this action'},

    'no_perm': {'status': 492, 'message': '[GAME] You cant do it'}
}


class NoMoneyError(Exception):
    pass


class MaxBuildingsCountReached(Exception):
    pass


class HasOwnerAlready(Exception):
    pass


class UHaveIt(Exception):
    pass


class UDontHaveIt(Exception):
    pass


class InDeal(Exception):
    pass


class LogWarning:
    def __init__(self, code, message_params=None):
        error = ERRORS[code].copy()
        self.message = (error['message'] % message_params) if message_params else error['message']

    def __unicode__(self):
        return self.message


class GameError(HttpResponse):
    def __init__(self, code, message_params=None):
        error = ERRORS[code].copy()
        error['message'] = (error['message'] % message_params) if message_params else error['message']
        super(GameError, self).__init__(json.dumps(error), content_type='application/json')


class SystemGameError(BaseException):
    def __init__(self, message):
        self.message = message
        super(SystemGameError, self).__init__()