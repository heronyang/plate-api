# -*- coding: utf-8 -*-

import uuid
import re
import logging

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from uuidfield import UUIDField
from django.contrib.auth.models import User, Group
from const import Urls
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError

logger = logging.getLogger(__name__)

RESTAURANT_NAME_MAX = 33
MEAL_NAME_MAX = 85

def is_valid_phone_number(phone_number):
    # only support cell phone number so far, like 0912123123
    if re.match(r'^09(\d{8})$', phone_number):
        return True
    return False

def is_valid_password(password):
    if re.match(r'^[A-Za-z0-9]{8,}$', password):
        return True
    return False

# FIXME: https://docs.djangoproject.com/en/dev/ref/contrib/auth/
# django.contrib.auth.User requires a alphanumeric 'username' field

class Configuration(models.Model):
    unit_test_mode = models.BooleanField()

    @classmethod
    def get0(cls):
        return cls.objects.get(pk=1)

def db_init(unit_test_mode=True):
    (vendor_group, vendor_group_created) = Group.objects.get_or_create(name='vendor')
    if vendor_group_created:
        vendor_group.save()
    (user_group, user_group_created) = Group.objects.get_or_create(name='user')
    if user_group_created:
        user_group.save()

    c = Configuration(unit_test_mode=unit_test_mode)
    c.save()

class Profile(models.Model):
    # additional info keyed on User
    user = models.OneToOneField(get_user_model())
    phone_number = models.CharField(max_length=20)
    pic_url = models.URLField(blank=True)

    @staticmethod
    def create(phone_number, password, role, add_registration=True):

        if not is_valid_phone_number(phone_number):
            raise IntegrityError('invalid phone number "%s"' % (phone_number,))

        if not is_valid_password(password):
            raise IntegrityError('invalid password')

        # FIXME: commit user, group, profile in same txn
        user = User.objects.create_user(username=phone_number, password=password)
        user.is_active = False
        user.save()

        group = Group.objects.get(name=role)
        group.user_set.add(user)

        profile = Profile(user=user,
                phone_number=phone_number)
        profile.save()

        if add_registration:
            m = profile.add_user_registration()
            c = Configuration.get0()
            if not c.unit_test_mode:
                profile.__send_verification_message(m)
        return profile

    def add_user_registration(self):
        '-> verification_msg'
        code = uuid.uuid4() #NOTE: this can be short if there's any other decode method
        ur = UserRegistration(user=self.user, code=code, ctime=timezone.now())
        ur.save()
        # FIXME: generate URL
        url = 'http://localhost:8000' + reverse('activate') + '?code=' + code.hex
        message = '歡迎加入Plate點餐的行列，點選一下連結以啟動帳號！ ' + url
        return message

    def activate(self):
        # set the user is_active
        self.user.is_active = True
        self.user.save()

        # set the registration record to clicked
        # all the past SMS sent from this user will no longer to active the account
        for ur in UserRegistration.objects.filter(user=self.user):
            ur.clicked = True
            ur.save()

    def __send_verification_message(self, msg):
        assert(0)

    def __unicode__(self):
        return self.phone_number

class Restaurant(models.Model):
    name = models.CharField(max_length=RESTAURANT_NAME_MAX)
    pic_url = models.URLField(blank=True)
    location = models.IntegerField(default=0) # Enum like

    # get the picture of the meal in HTML
    def pic_tag(self):
        if not self.pic_url:
            # return "image not found" image
            return u'<img width="200" src="%s" />' % Urls.EMPTY_PLATE_IMAGE_URL
        return u'<img width="200" src="%s" />' % self.pic_url
    pic_tag.short_description = "Restaurant Image"
    pic_tag.allow_tags = True

    # map the location to the real name
    def location_name(self):
        location_names = ["其他", "女二餐", "第二餐廳", "第一餐廳"]
        if len(location_names) > self.location:
            return location_names[self.location]
        return location_names[0]

    def __unicode__(self):
        return self.name

class Meal(models.Model):
    name = models.CharField(max_length=MEAL_NAME_MAX)
    pic_url = models.URLField(blank=True)
    price = models.IntegerField()
    restaurant = models.ForeignKey(Restaurant)
    status = models.IntegerField(default=0) # if sold out, or other status

    def __unicode__(self):
        return self.name

    # get the picture of the meal in HTML
    def pic_tag(self):
        if not self.pic_url:
            # return "image not found" image
            return u'<img width="200" src="%s" />' % Urls.EMPTY_PLATE_IMAGE_URL
        return u'<img width="200" src="%s" />' % self.pic_url
    pic_tag.short_description = "Meal Image"
    pic_tag.allow_tags = True

    def order_create(self, user, amount, time=None, note=None):
        # FIXME: meals could sell out
        if time is None:
            time = timezone.now()
        if note is None:
            note = ''
        order = Order(time=time, user=user, restaurant=self.restaurant)
        order.save()
        oi = OrderItem(meal=self, amount=amount, order=order, note=note)
        oi.save()
        return order

    def order_add(self, amount, order, note=None):
        # FIXME: meals could sell out
        if note is None:
            note = ''
        oi = OrderItem(meal=self, amount=amount, order=order, note=note)
        oi.save()

class Order(models.Model):
    #FIXME:add ctime, mtime
    time = models.DateTimeField('time entered')
    user = models.ForeignKey(get_user_model())
    restaurant = models.ForeignKey(Restaurant)
    pos_slip_number = models.IntegerField(blank=True, null=True) # the number printed on the slip by the Point-Of-Sale system
    status = models.IntegerField(default=0)

    def __unicode__(self):
        return '%s %s' % (self.user.username, self.restaurant.name)

    def delete(self):
        # NOTE: consider marking an order as "canceled" instead
        for i in self.orderitem_set.all():
            i.delete()
        super(Order, self).delete()


class OrderItem(models.Model):
    # NOTE: expect changes for business requirements
    meal = models.ForeignKey(Meal)
    amount = models.IntegerField()
    order = models.ForeignKey(Order)
    note = models.TextField(blank=True) # extra info for the order item

class MealRecommendation(models.Model):
    meal = models.ForeignKey(Meal)
    user = models.ForeignKey(get_user_model())
    description = models.TextField(blank=True) # extra info for the recommendation

    def __unicode__(self):
        return '%s %s' % (self.meal.name, self.user.username)

class UserRegistration(models.Model):
    code = UUIDField(auto=True)
    user = models.ForeignKey(get_user_model())
    clicked = models.BooleanField(default=False)
    ctime = models.DateTimeField('time entered')
