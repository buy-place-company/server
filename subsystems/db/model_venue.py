# -*- coding: utf-8 -*-
from django.db import models
from .model_user import User
import re


#TODO: properties
class VenueMock:
    def __init__(self, **kwargs):
        self.stats = {}
        if kwargs.get('location', ""):
            self.lat = kwargs['location']['lat']
            self.lng = kwargs['location']['lng']
        if kwargs.get('stats', ''):
            self.stats = {'checkin_count': kwargs['stats']['checkinsCount'],
                          'user_count': kwargs['stats']['usersCount'],
                          'tip_count': kwargs['stats']['tipCount']}
        if kwargs.get('name', ''):
            self.name = re.sub(r'[^a-zа-яA-ZА-Я]', "", kwargs['name'])
        if kwargs.get('id', ''):
            self.id = kwargs['id']

    def set_name(self, name):
        self.name = re.sub(r'[^a-zа-яA-ZА-Я ]', "", name)

    def save(self):
        print(self.lat)
        print(self.lng)
        print(self.stats)
        print(self.name)
        print(self.id)


class Venue(models.Model):
    #system fields
    list_id = models.CharField(max_length=255)
    #to return
    name = models.CharField(max_length=30)
    id = models.CharField(max_length=255, primary_key=True)
    checkin_count = models.IntegerField(default=0)
    user_count = models.IntegerField(default=0)
    tip_count = models.IntegerField(default=0)
    category = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    lvl = models.IntegerField(default=0)
    owner = models.ForeignKey(User, null=True, blank=True)
    price = models.IntegerField(default=10000)
