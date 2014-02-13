# -*- coding: utf-8 -*-

import uuid
import re
import logging
import json
import datetime
import urllib2
import pytz

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.timezone import is_naive as datetime_is_naive
from uuidfield import UUIDField
from django.contrib.auth.models import User, Group
from const import Urls
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from gcmclient import *
from const import Configs
from timezone_field import TimeZoneField
import tasks

from googl.short import GooglUrlShort

import warnings

warnings.filterwarnings('error', 'DateTimeField')

logger = logging.getLogger(__name__)

TIMEOUT_FOR_ADANDONED = (15 * 60)   # sec

RESISTER_WELCOME_MESSAGE = u"PLATE帳號啓用，請點連結: "

RESTAURANT_NAME_MAX = 33
LOCATION_NAME_MAX = 200
MEAL_NAME_MAX = 85
MEALCATEGORY_NAME_MAX = 85
COMMENT_MAX = 200
PASSWORD_MAX = 128
GCM_REGISTRATION_ID_MAX = 600

(RESTAURANT_STATUS_FOLLOW_OPEN_RULES,
 RESTAURANT_STATUS_MANUAL_OPEN,
 RESTAURANT_STATUS_MANUAL_CLOSE,
 RESTAURANT_STATUS_UNLISTED,
 ) = range(4)

(RESTAURANT_CLOSED_NEVER,
 RESTAURANT_CLOSED_EVERY_WEEKEND,
 RESTAURANT_CLOSED_EVERY_OTHER_WEEKEND,
 ) = range(3)

(ORDER_STATUS_INIT_COOKING, # order-incomplete
 ORDER_STATUS_FINISHED,     # order-incomplete
 ORDER_STATUS_PICKED_UP,    # order-complete
 ORDER_STATUS_REJECTED,     # order-complete
 ORDER_STATUS_ABANDONED,    # order-complete
 ORDER_STATUS_RESCUED,      # order-complete
 ORDER_STATUS_DROPPED       # order-complete
 ) = range(7)


def remove_incomplete_order():
    tasks.remove_incomplete_order.apply_async()

def gcm_send(gcm_registration_ids, title, message, ticker, username, collapse_key):
    # Construct (key => scalar) payload. do not use nested structures.
    data = {"title":title, "message":message, "ticker":ticker, "username":username}

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

class LastRegistrationTime(models.Model):
    user = models.ForeignKey(get_user_model())
    last_time = models.DateTimeField()

def db_init(unit_test_mode=True):
    (vendor_group, vendor_group_created) = Group.objects.get_or_create(name='vendor')
    if vendor_group_created:
        vendor_group.save()
    (user_group, user_group_created) = Group.objects.get_or_create(name='user')
    if user_group_created:
        user_group.save()

    c = Configuration(unit_test_mode=unit_test_mode)
    c.save()

class ClosedReason(models.Model):
    msg = models.TextField(blank=True)

    @staticmethod
    def create_defaults():
        ClosedReason(msg='非營業時間').save()
        ClosedReason(msg='商家忙碌中').save()
        ClosedReason(msg='提早關門').save()
        ClosedReason(msg='特殊休假').save()

    def __unicode__(self):
        return self.msg

class Location(models.Model):
    name = models.CharField(max_length=LOCATION_NAME_MAX)
    timezone = TimeZoneField()

    def __unicode__(self):
        return self.name

class Restaurant(models.Model):
    name = models.CharField(max_length=RESTAURANT_NAME_MAX)
    pic_url = models.URLField(blank=True)
    location = models.ForeignKey(Location)
    status = models.IntegerField(default=0) # Enum like

    # increase 1 when 1 order is added, no need to reset this field
    number_slip = models.IntegerField(default=0)

    # last number of the continous number slips
    current_number_slip = models.IntegerField(default=0) # the last continous number slip
    capacity = models.IntegerField(default=99)

    #
    closed_reason = models.ForeignKey(ClosedReason, null=True)
    closed_rule = models.IntegerField(default=0)    #Enum like
    closed_every_other_weekend_initial_closed_weekend_sat = models.DateField(default=datetime.date(2014, 1, 4), null=True)

    #
    description = models.TextField(blank=True) # extra info for the recommendation

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
    # not using
    def location_name(self):
        location_names = ["其他", "女二餐", "第二餐廳", "第一餐廳"]
        if len(location_names) > self.location:
            return location_names[self.location]
        return location_names[0]

    def prior_notification(self):
        prior_ns = self.current_number_slip + Configs.PRIOR_NUMBER_SLIPS
        os = Order.objects.filter(restaurant=self)
        for o in os:
            if o.pos_slip_number == prior_ns:
                p = o.user.profile
                p.send_notification(caller='prior_notification', method='gcm')

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

        self.prior_notification()
    #
    def current_cooking_orders(self):
        os = Order.objects.filter(restaurant=self)
        n = 0
        for i in os:
            if i.status == ORDER_STATUS_INIT_COOKING:
                n += 1
        return n

    def status_set(self, status):
        if status == RESTAURANT_STATUS_FOLLOW_OPEN_RULES:
            self.closed_reason = ClosedReason.objects.get(pk=1)

        self.status = status
        self.save()

    def closed_reason_set(self, closed_reason):
        cr = ClosedReason.objects.get(pk=closed_reason)
        self.closed_reason = cr
        self.save()

    @property
    def closed_reason_msg(self):
        return self.closed_reason.msg

    def is_open_on(self, dtime):
        if self.status != RESTAURANT_STATUS_FOLLOW_OPEN_RULES:
            if self.status == RESTAURANT_STATUS_MANUAL_OPEN:
                return True
            else:
                return False

        location_tz = self.location.timezone
        if datetime_is_naive(dtime):
            dtime = dtime.replace(tzinfo=location_tz)

        if is_closed_on_rule(dtime.date(), self.closed_rule, self.closed_every_other_weekend_initial_closed_weekend_sat):
            return False

        holidays = RestaurantHoliday.objects.filter(restaurant=self)
        for h in holidays:
            if h.closed_date == dtime.date():
                return False

        ohs = RestaurantOpenHours.objects.filter(restaurant=self)
        if not ohs:
            # empty open hours list indicates 24 hr restaurants, e.g. 7-11
            return True

        for oh in ohs:
            (s, e) = (oh.start.replace(tzinfo=location_tz), oh.end.replace(tzinfo=location_tz))
            if dtime.time() >= s and dtime.time() <= e:
                return True

        return False

    @property
    def is_open(self):
        return self.is_open_on(timezone.now())

    def set_open_hours_for_test(self, open_hours):
        RestaurantOpenHours.objects.filter(restaurant=self).delete()
        for oh in open_hours:
            (s, e) = oh
            # Storing as timezone naive (i.e. non timezone aware) time objects for SQLite
            # Will convert to timezone aware times in 'Restaurant.is_open'
            start = datetime.time(s / 100, s % 100)
            end = datetime.time(e / 100, e % 100)
            roh = RestaurantOpenHours(restaurant=self, start=start, end=end)
            roh.save()

    def set_scheduled_holidays_for_test(self, holidays):
        RestaurantHoliday.objects.filter(restaurant=self).delete()
        location_tz = self.location.timezone
        for i in holidays:
            RestaurantHoliday(restaurant=self, closed_date=i).save()

    def __unicode__(self):
        return self.name

class VendorLastRequestTime(models.Model):
    restaurant = models.ForeignKey(Restaurant)
    last_time = models.DateTimeField()

class RestaurantOpenHours(models.Model):
    restaurant = models.ForeignKey(Restaurant)
    start = models.TimeField()
    end = models.TimeField()

class RestaurantHoliday(models.Model):
    restaurant = models.ForeignKey(Restaurant)
    closed_date = models.DateField()

def is_weekend(date):
    return date.isoweekday() in [6, 7]

def is_closed_on_rule(date, closed_rule, init_closed_weekend):
    if closed_rule == RESTAURANT_CLOSED_EVERY_WEEKEND:
        return is_weekend(date)
    elif closed_rule == RESTAURANT_CLOSED_EVERY_OTHER_WEEKEND:
        if not is_weekend(date):
            return False

        day1 = (date - datetime.timedelta(days=date.weekday()))
        day2 = (init_closed_weekend - datetime.timedelta(days=init_closed_weekend.weekday()))
        weeks = (day2 - day1).days / 7

        if (weeks % 2) == 0:
            return True
        else:
            return False

    return False

class Profile(models.Model):
    # additional info keyed on User
    user = models.OneToOneField(get_user_model())
    phone_number = models.CharField(max_length=20)
    pic_url = models.URLField(blank=True)
    ctime = models.DateTimeField(auto_now_add=True)

    failure = models.IntegerField(default=0)
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
        elif caller is 'pickup':
            title = '已領餐'
            message = '餐點已經順利領取，感謝使用Plate點餐系統'
            ticker = message
            collapse_key = 'order_pickuped'
        elif caller is 'failure':
            title = '未領餐'
            message = '嗨，很可惜您今天沒有領餐，將計上一次失敗記錄，第二次失敗便不能再點餐'
            ticker = message
            collapse_key = 'order_failure'
        elif caller is 'prior_notification':
            title = '快好了'
            message = '快輪到您領餐了！'
            ticker = message
            collapse_key = 'prior_notification'
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
                     username=self.user.username,
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
        gs = GCMRegistrationId.objects.filter(gcm_registration_id=gcm_registration_id)
        is_exist = False
        for g in gs:
            if g.user == self.user:
                is_exist = True
        if not is_exist:
            gr = GCMRegistrationId(user=self.user, gcm_registration_id=gcm_registration_id)
            gr.save()

        # FIXME: generate URL
        url = url_prefix + reverse('activate') + '?c=' + code.hex
        surl = GooglUrlShort(url).short()
        message = RESISTER_WELCOME_MESSAGE + surl
        return message

    def free_to_order(self):
        orders = Order.objects.filter(user=self.user)
        for i in orders:
            if i.status == ORDER_STATUS_FINISHED or i.status == ORDER_STATUS_INIT_COOKING:
                return False
        return True

    def send_verification_message(self, msg, phone_number):
        international_phone_number = "+886" + phone_number[1:] # 09xx... => +8869xx...

        tasks.sms_send.delay(international_phone_number, msg)
        """
        client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        try:
            sms = client.sms.messages.create(body=msg,
                                             to=international_phone_number,
                                             from_=TWILIO_PHONE_NUMBER)
        except TwilioRestException as Ex:
            return (False, Ex.code)
        else:
            return (True, None)
        # assert(0)
        """

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
        # NOTE: this function is turned off for MVP
        #tasks.abandon.apply_async((self.id,), countdown=TIMEOUT_FOR_ADANDONED)

        # update restaurant current_number_slip
        self.restaurant.update_current_number_slip(self.pos_slip_number)

        return True

    def pickup(self):
        if self.status == ORDER_STATUS_FINISHED:
            self.status = ORDER_STATUS_PICKED_UP
            self.save()
            p = self.user.profile
            p.send_notification(caller='pickup', method='gcm')
            return True
        if self.status == ORDER_STATUS_ABANDONED:
            self.status = ORDER_STATUS_RESCUED
            self.save()
            p = self.user.profile
            p.send_notification(caller='pickup', method='gcm')
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

        self.restaurant.update_current_number_slip(self.pos_slip_number)
        return True

    @classmethod
    def daily_cleanup(cls):
        logger.info('Order.daily_cleanup: ' + str(timezone.now()))
        os = Order.objects.all()
        for o in os:
            if o.status == ORDER_STATUS_FINISHED:
                p = o.user.profile
                p.failure += 1
                p.save()

                p.send_notification(caller='failure', method='gcm')
                o.status = ORDER_STATUS_ABANDONED
                o.save()

            elif o.status == ORDER_STATUS_INIT_COOKING:
                # no need for gcm here
                o.status = ORDER_STATUS_DROPPED
                o.save()


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
