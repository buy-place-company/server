# -*- coding: utf-8 -*-
import datetime
from django.utils.timezone import now
from django.db import models
from subsystems.db.model_user import User
from subsystems.db.model_venue import Venue


STATES = (
    ('incomplete', 'Uncompleted'),
    ('complete', 'Completed'),
    ('rejected', 'Rejected'),  # By user_to
    ('revoke', 'Revoked')  # By user_from
)

TYPES = (
    ('WTB', 'Want to buy'),
    ('WTS', 'Want to sell'),
    ('WTT', 'Want to trade'),
)


class Deal(models.Model):
    venue = models.ForeignKey(Venue, to_field='venue_id', help_text='Сделка на здание')
    user_from = models.ForeignKey(User, help_text="Сделку предложил", related_name='user_from')
    user_to = models.ForeignKey(User, help_text="Сделку предложили", related_name='user_ro')
    amount = models.IntegerField(help_text='Сумма сделки')
    date_added = models.DateTimeField(help_text='Дата предложения')
    date_expire = models.DateTimeField(help_text='Дата истечения срока предложения')
    state = models.CharField(help_text='Состояние', max_length=10, choices=STATES, default=False)
    dtype = models.CharField(help_text='Тип предложения', max_length=10, choices=TYPES, default=False)
    is_public = models.BooleanField(help_text='Доступна всем?', default=False)

    def serialize(self, user=None, **kwargs):
        return {
            'id': self.pk,
            'venue': self.venue.serialize(is_public=(user == self.user_from) if user and self.user_from else False),
            'user_from': self.user_from.serialize(is_public=(user == self.user_from) if user and self.user_from else False),
            'user_to': self.user_to.serialize(is_public=(user == self.user_to) if user and self.user_to else False),
            'amount': self.amount,
            'date_added': str(self.date_added.strftime('%Y-%m-%d %H:%M:%S')),
            'date_expired': str(self.date_expire.strftime('%Y-%m-%d %H:%M:%S')),
            'type': self.get_dtype_display(),
            'status': self.get_state_display()
        }

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.id:
            self.date_added = now()
            self.date_expire = now() + datetime.timedelta(days=7)
        super(Deal, self).save(force_insert, force_update, using, update_fields)
