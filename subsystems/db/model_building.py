from django.db import models
from .model_user import User


class Building(models.Model):
    title = models.CharField(max_length=30)
    checkin_count = models.IntegerField(default=0)
    owner = models.ForeignKey(User, null=True, blank=True)
    # position, venueID, other values
