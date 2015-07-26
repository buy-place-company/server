import hashlib
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import ForeignKey
from subsystems.db.model_user import User
from subsystems.db.model_venue import Venue


class Bookmark(models.Model):
    # system fields
    user = ForeignKey(User)
    venue = ForeignKey(Venue)
    push_check_sum = models.CharField(max_length=33)
    is_autocreated = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        m = hashlib.md5()
        m.update(self.content_object.check_sum.encode('utf-8'))
        self.push_check_sum = m.hexdigest()
        super(Bookmark, self).save(*args, **kwargs)

    def serialize(self, user_owner=None, **kwargs):
        return {
            'user': self.user.serialize(user_owner=user_owner),
            str(self.content_type): self.content_object.serialize(user_owner=user_owner, **kwargs),
        }
