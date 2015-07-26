from .model_user import User
from .model_venue import Venue
from .model_zone import Zone
from .model_deal import Deal
import hashlib
from django.db import models as mo
from django.db.models import ForeignKey


class Bookmark(mo.Model):
    # system fields
    user = ForeignKey(User)
    venue = ForeignKey(Venue)
    push_check_sum = mo.CharField(max_length=33)
    is_autocreated = mo.BooleanField(default=True)

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
