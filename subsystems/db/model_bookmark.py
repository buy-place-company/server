import hashlib
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import ForeignKey
from subsystems.db.model_user import User


class BookmarkManager(models.Manager):
    def get_or_create(self, user, content_object, is_autocreated=True):
        try:
            bookmark = self.get(user=user, content_type=ContentType.objects.get_for_model(type(content_object)),
                                object_id=content_object.pk)
        except Bookmark.DoesNotExist:
            bookmark = self.create(user=user, content_object=content_object, is_autocreated=is_autocreated)
        return bookmark


class Bookmark(models.Model):
    # system fields
    user = ForeignKey(User)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    push_check_sum = models.CharField(max_length=33)
    is_autocreated = models.BooleanField(default=True)

    # Manager
    objects = BookmarkManager()

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
