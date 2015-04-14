from django.db import models


class Zone(models.Model):
    list_id = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    lat = models.FloatField()
    lng = models.FloatField()