# -*- coding: utf-8 -*-
import datetime
from django.utils.timezone import now
from django.db import models
from subsystems.db.model_user import User
from subsystems.db.model_venue import Venue


class Deal(models.Model):
    venue = models.ForeignKey(Venue, to_field='venue_id', help_text='Сделка на здание')
    user_from = models.ForeignKey(User, help_text="Сделку предложил", related_name='user_from')
    user_to = models.ForeignKey(User, help_text="Сделку предложили", related_name='user_ro')
    amount = models.IntegerField(help_text='Сумма сделки')
    date_added = models.DateTimeField(help_text='Дата предложения')
    date_expire = models.DateTimeField(help_text='Дата истечения срока предложения')
    is_complete = models.BooleanField(help_text='Сделка закончена?', default=False)

    def serialize(self, user=None):
        return {
            'venue': self.venue.serialize(is_public=(user == self.user_from) if user and self.user_from else False),
            'user_from': self.user_from.serialize(is_public=(user == self.user_from) if user and self.user_from else False),
            'user_to': self.user_from.serialize(is_public=(user == self.user_to) if user and self.user_from else False),
            'amount': self.amount,
            'date_added': str(self.date_added.strftime('%Y-%m-%d %H:%M:%S')),
            'date_expired': str(self.date_expire.strftime('%Y-%m-%d %H:%M:%S')),
        }

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.date_added = now()
        self.date_expire = now() + datetime.timedelta(days=7)
        super(Deal, self).save(force_insert, force_update, using, update_fields)
