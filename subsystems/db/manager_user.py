import json
import urllib.request
from django.db import models
from subsystems._auth import authenticate, login


class UserManager(models.Manager):
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

    def create_user(self, email=None, password=None, is_superuser=False, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        if email is not None:
            email = self.normalize_email(email)
        user = self.model(email=email, is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_and_auth_vk(self, request, id_vk):
        try:
            user = self.get(id_vk=id_vk)
        except:
            url = \
                "https://api.vk.com/method/users.get?" + \
                "user_ids=%d&" % id_vk + \
                "v=5.33"

            conn = urllib.request.urlopen(url)
            data = json.loads(conn.read().decode('utf_8'))['response']
            name = '{0} {1}'.format(data[0]['first_name'], data[0]['last_name'])

            user = self.create(id_vk=id_vk, name=name)
            user.set_password("")
            user.save()

        user = authenticate(username=user.id, password="")
        login(request, user)
        return user