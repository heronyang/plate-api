# -*- coding: utf-8 -*-

import uuid
import re
import logging
import json
import urllib2

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from uuidfield import UUIDField
from django.contrib.auth.models import User, Group
from const import Urls
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from gcmclient import *
import tasks

logger = logging.getLogger(__name__)

TIMEOUT_FOR_ADANDONED = (15 * 60)   # sec

RESTAURANT_NAME_MAX = 33
MEAL_NAME_MAX = 85
MEALCATEGORY_NAME_MAX = 85
COMMENT_MAX = 200
PASSWORD_MAX = 128
GCM_REGISTRATION_ID_MAX = 600

(ORDER_STATUS_INIT_COOKING,
 ORDER_STATUS_FINISHED,
 ORDER_STATUS_PICKED_UP,
 ORDER_STATUS_REJECTED,
 ORDER_STATUS_ABANDONED,
 ORDER_STATUS_RESCUED) = range(6)

def gcm_send(gcm_registration_ids, title, message, ticker, collapse_key):
    # Construct (key => scalar) payload. do not use nested structures.
    data = {"title":title, "message":message, "ticker":ticker, }

    # Unicast or multicast message, read GCM manual about extra options.
    # It is probably a good idea to always use JSONMessage, even if you send
    # a notification to just 1 registration ID.
    multicast = JSONMessage(gcm_registration_ids, data, collapse_key=collapse_key, dry_run=False)
    tasks.gcm_send.delay(multicast)

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

class Restaurant(models.Model):
    name = models.CharField(max_length=RESTAURANT_NAME_MAX)
    pic_url = models.URLField(blank=True)
    location = models.IntegerField(default=0) # Enum like
    status = models.IntegerField(default=0) # Enum like

    # increase 1 when 1 order is added, no need to reset this field
    number_slip = models.IntegerField(default=0)

    # last number of the continous number slips
    current_number_slip = models.IntegerField(default=0) # the last continous number slip
    capacity = models.IntegerField(default=99)

    def new_number_slip(self):
        self.number_slip += 1
        self.save()
        return self.number_slip

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

    #
    def update_current_number_slip(self, pos_slip_number):

        os = Order.objects.filter(restaurant=self)
        if not os:
            return

        cur_ns = self.current_number_slip

        # FIXME: use Order.objects.filter(restaurant=self && pos_slip_number=(cur_ns+1)) instead
        while True:
            updated = False
            for i in os:
                if i.status == ORDER_STATUS_INIT_COOKING:
                    continue
                if i.pos_slip_number == (cur_ns+1):
                    cur_ns += 1
                    self.current_number_slip = cur_ns
                    self.save()
                    updated = True
            if not updated:
                break

    def __unicode__(self):
        return self.name

class Profile(models.Model):
    # additional info keyed on User
    user = models.OneToOneField(get_user_model())
    phone_number = models.CharField(max_length=20)
    pic_url = models.URLField(blank=True)
    ctime = models.DateTimeField(auto_now_add=True)

    # for users in vendor group
    restaurant = models.ForeignKey(Restaurant, null=True)

    @staticmethod
    def get_or_create(phone_number, role, add_registration=True):
        if not is_valid_phone_number(phone_number):
            raise IntegrityError('invalid phone number "%s"' % (phone_number,))

        try:
            profile = Profile.objects.get(phone_number=phone_number)
        except Profile.DoesNotExist:
            pass
        else:
            return (profile, False)

        # FIXME: commit user, group, profile in same txn
        user = User.objects.create_user(username=phone_number, password='')
        user.is_active = False
        user.save()

        group = Group.objects.get(name=role)
        group.user_set.add(user)

        profile = Profile(user=user, phone_number=phone_number)
        profile.save()
        return (profile, True)

    def send_notification(self, caller, method):
        collapse_key = ''
        if caller is 'finish':
            title = '餐點完成'
            message = '您的餐點做好啦！'
            ticker = message
            collapse_key = 'order_finished'
        elif caller is 'cancel':
            title = '點餐失敗'
            message = '抱歉老闆因故無法完成訂單！'
            ticker = message
            collapse_key = 'order_canceled'
        else:
            raise TypeError()

        #gcm_registration_ids = GCMRegistrationId.objects.filter(user=self.user)
        gcm_registration_ids = []
        gs = GCMRegistrationId.objects.filter(user=self.user)
        for g in gs:
            gcm_registration_ids.append(g.gcm_registration_id)

        if method is 'gcm':
            gcm_send(gcm_registration_ids=gcm_registration_ids,
                     title=title,
                     message=message,
                     ticker=ticker,
                     collapse_key=collapse_key)
        else:
            raise TypeError()


    def add_user_registration(self, url_prefix, gcm_registration_id, password=None, raw_password=None):
        if (password is None) and (raw_password is None):
            raise TypeError()

        if gcm_registration_id is None:
            raise TypeError()

        if password is None:
            h = PBKDF2PasswordHasher()
            password = h.encode(raw_password, h.salt())

        code = uuid.uuid4() #NOTE: this can be short if there's any other decode method
        ur = UserRegistration(code=code, user=self.user, password=password, ctime=timezone.now())
        ur.save()

        # avoid duplication
        if not GCMRegistrationId.objects.filter(gcm_registration_id=gcm_registration_id):
            gr = GCMRegistrationId(user=self.user, gcm_registration_id=gcm_registration_id)
            gr.save()

        # FIXME: generate URL
        url = url_prefix + reverse('activate') + '?code=' + code.hex
        message = '歡迎加入Plate點餐的行列，點選一下連結以啟動帳號！ ' + url
        return message

    def __send_verification_message(self, msg):
        assert(0)

    def __unicode__(self):
        return self.phone_number

class MealCategory(models.Model):
    name = models.CharField(max_length=MEALCATEGORY_NAME_MAX)

    def __unicode__(self):
        return self.name

class GCMRegistrationId(models.Model):
    user = models.ForeignKey(get_user_model())
    gcm_registration_id = models.CharField(max_length=GCM_REGISTRATION_ID_MAX)

    def __unicode__(self):
        return self.user.username

class Meal(models.Model):
    name = models.CharField(max_length=MEAL_NAME_MAX)
    pic_url = models.URLField(blank=True)
    price = models.IntegerField()
    restaurant = models.ForeignKey(Restaurant)
    status = models.IntegerField(default=0) # if sold out, or other status
    meal_category = models.ForeignKey(MealCategory, null=True)

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
        if note is None:
            note = ''

        number_slip = self.restaurant.new_number_slip()

        order = Order(user=user, restaurant=self.restaurant, pos_slip_number=number_slip, status=ORDER_STATUS_INIT_COOKING)
        order.save()
        oi = OrderItem(meal=self, amount=amount, order=order, note=note)
        oi.save()

        # generate a number slip
        return (order, number_slip)

    def order_add(self, amount, order, note=None):
        # FIXME: meals could sell out
        if note is None:
            note = ''
        oi = OrderItem(meal=self, amount=amount, order=order, note=note)
        oi.save()

class Order(models.Model):
    #time = models.DateTimeField('time entered')
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(get_user_model())
    restaurant = models.ForeignKey(Restaurant)
    pos_slip_number = models.IntegerField(blank=True, null=True) # the number printed on the slip by the Point-Of-Sale system
    status = models.IntegerField(default=0)

    user_comment = models.CharField(max_length=COMMENT_MAX, blank=True)
    vendor_comment = models.CharField(max_length=COMMENT_MAX, blank=True)

    def __unicode__(self):
        return '%s %s' % (self.user.username, self.restaurant.name)

    def delete(self):
        # NOTE: consider marking an order as "canceled" instead
        for i in self.orderitem_set.all():
            i.delete()
        super(Order, self).delete()

    def finish(self):
        if self.status != ORDER_STATUS_INIT_COOKING:
            return False
        self.status = ORDER_STATUS_FINISHED
        self.save()

        #
        p = self.user.profile
        p.send_notification(caller='finish', method='gcm')

        # turn the order to abandon in (TIMEOUT_FOR_ADANDONED) seconds
        # if the user does not 'pickup' during this period
        tasks.abandon.apply_async((self.id,), countdown=TIMEOUT_FOR_ADANDONED)

        # update restaurant current_number_slip
        self.restaurant.update_current_number_slip(self.pos_slip_number)

        return True

    def pickup(self):
        if self.status == ORDER_STATUS_FINISHED:
            self.status = ORDER_STATUS_PICKED_UP
            self.save()
            return True
        if self.status == ORDER_STATUS_ABANDONED:
            self.status = ORDER_STATUS_RESCUED
            self.save()
            return True
        #
        return False

    def cancel(self):
        if self.status != ORDER_STATUS_INIT_COOKING:
            return False

        self.status = ORDER_STATUS_REJECTED
        self.save()

        #
        p = self.user.profile
        p.send_notification(caller='cancel', method='gcm')

        return True


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
    password = models.CharField(max_length=PASSWORD_MAX)
    clicked = models.BooleanField(default=False)
    ctime = models.DateTimeField('time entered', auto_now=True)

    def activate(self):
        if self.clicked:
            raise IntegrityError('Already activated')
        self.clicked = True
        self.save()
        user = self.user
        user.is_active = True
        user.save()

        # FIXME: DevicePassword
