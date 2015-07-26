from .model_user import User
from .model_venue import Venue
from .model_zone import Zone
from .model_bookmark import Bookmark
from .model_deal import Deal


class DataBase:
    Bookmark = Bookmark
    Deal = Deal
    Zone = Zone
    Venue = Venue
    User = User