from subsystems.api.errors import GameError


def auth_required(fn):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return GameError('no_auth')
        return fn(request, *args, **kwargs)
    return wrapper