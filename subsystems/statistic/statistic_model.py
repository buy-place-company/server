from django.db import models


class Statistic(models.Model):
    zone_id = models.IntegerField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    counter = models.IntegerField(default=0)