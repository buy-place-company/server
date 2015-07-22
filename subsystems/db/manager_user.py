import json
import urllib.request
from django.db import models
from subsystems._auth import authenticate, login


class UserManager(models.Manager):
    DEFAULT_AUTH_BACKEND = 'django.contrib.auth.backends.ModelBackend'

    @classmethod
    def normalize_email(cls, email):
        """
        Normalize the address by lowercasing the domain part of the email
        address.
        """
        email = email or ''
        try:
            email_name, domain_part = email.strip().rsplit('@', 1)
        except ValueError:
            pass
        else:
            email = '@'.join([email_name, domain_part.lower()])
        return email

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    def create_and_auth_email(self, request, email, password, name):
        email = self.normalize_email(email)

        user = self.model(email=email, name=name)
        user.set_password(password)
        user.save(using=self._db)

        user.backend = self.DEFAULT_AUTH_BACKEND
        login(request, user)
        return user

    def create_and_auth_vk(self, request, id_vk, name):
        user = self.create(id_vk=id_vk, name=name)
        user.set_password(None)
        user.save()

        user.backend = self.DEFAULT_AUTH_BACKEND
        login(request, user)
        return user

    def auth(self, request, user, **kwargs):
        if 'password' in kwargs:
            user = authenticate(id=user.id, password=kwargs['password'])
            if user is None:
                return None
        else:
            user.backend = self.DEFAULT_AUTH_BACKEND
        login(request, user)
        return user
