from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_save
from django.dispatch import receiver
from subsystems.db.model_bookmark import Bookmark
from subsystems.db.model_venue import Venue

@receiver(pre_save, sender=Venue)
def my_handler(sender, instance, **kwargs):
    print(Bookmark.objects.filter(content_type=ContentType.objects.get_for_model(sender), object_id=instance.pk))
