from django.db import models


class Zone(models.Model):
    list_id = models.CharField(max_length=255)
    lat = models.FloatField()
    lng = models.FloatField()