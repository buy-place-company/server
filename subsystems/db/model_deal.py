# -*- coding: utf-8 -*-
import datetime
from django.utils.timezone import now
from django.db import models
from subsystems.db import models as mo


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
    venue = models.ForeignKey(mo.Venue, to_field='venue_id', help_text='Сделка на здание')
    user_from = models.ForeignKey(mo.User, help_text="Сделку предложил", related_name='user_from')
    user_to = models.ForeignKey(mo.User, help_text="Сделку предложили", related_name='user_ro', null=True)
    amount = models.IntegerField(help_text='Сумма сделки')
    date_added = models.DateTimeField(help_text='Дата предложения')
    date_expire = models.DateTimeField(help_text='Дата истечения срока предложения')
    state = models.CharField(help_text='Состояние', max_length=11, choices=STATES)
    dtype = models.CharField(help_text='Тип предложения', max_length=10, choices=TYPES)
    is_public = models.BooleanField(help_text='Доступна всем?', default=False)

    @property
    def push_id(self):
        return self.pk

    @property
    def check_sum(self):
        return ''.join([str(self.user_to.id if self.user_to else ''), str(self.user_from.id),
                        str(self.amount), str(self.get_state_display()), str(self.date_expire)])

    def serialize(self, user_owner=None, **kwargs):
        return {
            'id': self.pk,
            'venue': self.venue.serialize(user_owner=user_owner),
            'user_from': self.user_from.serialize(user_owner=user_owner),
            'user_to': self.user_to.serialize(user_owner=user_owner) if self.user_to is not None else None,
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
