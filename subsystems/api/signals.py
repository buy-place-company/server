from django.db.models.signals import pre_save
from django.dispatch import receiver
from subsystems.db.model_venue import Venue

@receiver(pre_save, sender=Venue)
def my_handler(sender, instance, **kwargs):
    print("Pre save")
    print(instance)
