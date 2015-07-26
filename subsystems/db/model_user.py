from django.contrib.auth.hashers import make_password, check_password
from django.db import models
import bisect
from conf.settings_game import START_CASH_AMOUNT
from conf.settings import STATIC_URL
from conf.settings_local import SettingsLocal
from .manager_user import UserManager

EXP_MAP = [68, 295, 805, 1716, 3154, 5249, 8136, 11955, 16851, 22973, 30475,
           39516, 50261, 62876, 77537, 94421, 113712, 135596, 160266, 84495,
           95074, 107905, 123472, 142427, 165669, 194509, 231086, 279822, 374430, 
           209536, 248781, 296428, 354546, 425860, 514086, 624568, 765820, 954872, 
           1312934, 376794, 570584, 702247, 864268, 1064437, 1313189, 1625260, 
           2023672, 2553793, 3540654, 1628580, 2030288, 2525315, 3136966, 3895327, 
           4840361, 6059118, 7618511, 9695807, 13539939, 7827912, 9820182, 12274327, 
           15304458, 19055275, 23715366, 29732457, 37394453, 47531372, 55129381, 
           47864070, 59155067, 73265903, 90895887, 112918193, 140457133, 175038441, 
           224130847, 275229537, 374922035, 433175886, 519071722, 616520968, 732660914, 
           867504463, 5906525385, 8207524971, 14341344002, 9969088216, 18392059298, 
           22570174524, 27893873314, 34494700219, 42704220933, 52959289091, 100973118145, 
           195410550016, 384956596063, 777809067883]


class User(models.Model):
    # ========== user auth information ==========
    id = models.AutoField(primary_key=True)
    id_vk = models.BigIntegerField(null=True)
    password = models.CharField(max_length=128, null=True)
    is_superuser = models.BooleanField(default=False)
    email = models.EmailField(max_length=60, unique=True, null=True)
    name = models.CharField(max_length=60)
    signup_date = models.DateField(auto_now_add=True)
    buildings_count = models.SmallIntegerField(default=0)
    cash = models.IntegerField(default=START_CASH_AMOUNT)
    _score = models.IntegerField(default=0)
    USERNAME_FIELD = 'id'

    objects = UserManager()

    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=["password"])
        return check_password(raw_password, self.password, setter)

    def serialize(self, is_public=True, **kwargs):
        user = kwargs.pop('user_owner', None)
        response = {
            "id": self.id,
            "username": self.name,
            "level": self.lvl,
            "avatar": '{0}{1}{2}.png'.format(SettingsLocal.DOMAIN_RAW, STATIC_URL, self.id),
            "score": self.score,
            "objects_count": self.buildings_count,
            "max_objects": self.max_objects,
        }

        if not is_public or user and user == self:
            response.update({
                "cash": self.cash,
            })

        return response

    @property
    def lvl(self):
        return bisect.bisect_right(EXP_MAP, int(self.score / 1000))

    @property
    def max_objects(self):
        return 2 + int(self.lvl * 5 + round(1.3 ** self.lvl))

    @property
    def score(self):
        from subsystems.db.model_venue import Venue
        score = round(self.cash * 0.8)
        for obj in Venue.objects.filter(owner=self):
            score += obj.expense
        self._score = score
        return score

    def has_place(self):
        print(self.max_objects, self.buildings_count)
        return self.max_objects == self.buildings_count
