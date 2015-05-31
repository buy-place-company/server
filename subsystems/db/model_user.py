from django.contrib.auth.hashers import make_password, check_password
from django.db import models

from .manager_user import UserManager


class User(models.Model):
    # ========== user auth information ==========
    id = models.AutoField(primary_key=True)
    id_vk = models.IntegerField(null=True)
    password = models.CharField(max_length=128, null=True)
    is_superuser = models.BooleanField(default=False)
    email = models.EmailField(max_length=30, unique=True, null=True)
    name = models.CharField(max_length=30)
    signup_date = models.DateField(auto_now_add=True)
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

    # ========== user game information ==========
    # public
    experience_count = models.BigIntegerField(default=0)
    buildings_count = models.SmallIntegerField(default=0)
    score = models.IntegerField(default=0)
    avatar = models.URLField()
    # private
    cash = models.IntegerField(default=0)

    def serialize(self, is_public=True):
        response = {
            "id": self.id,
            "username": self.name,
            "level": self.lvl,
            "avatar": self.avatar,
            "score": self.score,
            "objects_count": self.buildings_count,
            "max_objects": self.max_objects,
            "experience": self.experience_count,
        }

        if not is_public:
            response.update({
                "cache": 12,
            })

    @property
    def score(self):
        return self.cash

    @property
    def max_objects(self):
        return self.lvl * 5 + round(1.3 ** self.lvl)