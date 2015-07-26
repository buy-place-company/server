from django.core.management import BaseCommand
from subsystems.db.model_user import User
from subsystems.db.model_venue import Venue


class Command(BaseCommand):
    help = 'Update zones'

    def handle(self, *args, **kwargs):
        for user in User.objects.all():
            user.building_counter = len(Venue.objects.filter(owner=self))