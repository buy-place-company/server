from django.contrib.auth.hashers import make_password, check_password
from django.db import models

from .manager_user import UserManager
from conf.settings_game import SettingsGame


class User(models.Model):
    # ========== user auth information ==========

    id = models.AutoField(primary_key=True)

    password = models.CharField(max_length=128)
    is_superuser = models.BooleanField(default=False)

    email = models.EmailField(max_length=30, unique=True)
    name = models.CharField(max_length=30)

    signup_date = models.DateField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'

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

    experience_count = models.BigIntegerField(default=0)
    money_payed_amount = models.BigIntegerField(default=0)
    money_amount = models.BigIntegerField(default=START_MONEY_AMOUNT)
    buildings_count = models.SmallIntegerField(default=0)