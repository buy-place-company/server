# -*- coding: utf-8 -*-
import json
from django.http import HttpResponse

ERRORS = {
    # System errors
    ## No args
    'no_args': {'status': 400, 'message': '[SYS] Not enough args: %s'},
    'no_action': {'status': 401, 'message': '[SYS] No such action'},
    'no_venue': {'status': 402, 'message': '[SYS] No such venue'},
    'no_deal': {'status': 403, 'message': '[SYS] No such deal'},
    ## Wrong type/format
    'wrong_args': {'status': 421, 'message': '[SYS] Wrong args: %s'},
    ## Other
    'no_auth': {'status': 491, 'message': '[SYS] Unauthorized access'},

    # Partners errors
    'VK': {'status': 300, 'message': '[VK] %s'},
    'VK_no_auth': {'status': 301, 'message': '[VK] HTTP Error 401: Unauthorized'},

    # Game errors
    ## Users
    'no_money': {'status': 201, 'message': '[GAME] No money for this action'},
    ## Buildings
    'owner_exists': {'status': 211, 'message': '[GAME] The building has owner already'},
    'already_have': {'status': 212, 'message': '[GAME] You have this building already'},
    'dont_have': {'status': 213, 'message': '[GAME] You dont have this building yet'},
    'no_owner': {'status': 214, 'message': '[GAME] No one doesnt have this building yet'},
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
