"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import json

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

import api.models
from api.models import *

(ORDER_STATUS_INIT_COOKING,
 ORDER_STATUS_FINISHED,
 ORDER_STATUS_PICKED_UP,
 ORDER_STATUS_REJECTED,
 ORDER_STATUS_ABANDONED,
 ORDER_STATUS_RESCUED) = range(6)

PHONE_NUMBER1 = '0911111111'
PHONE_NUMBER2 = '0922222222'
PHONE_NUMBER3 = '0933333333'

GCM_REGISTRATION_ID0 = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-1234567890'
GCM_REGISTRATION_ID1 = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-12345678900987654321'

class _User0(object):
    phone_number = '0912345678'
    username = phone_number
    password = 'u0pw1234'
    gcm_registration_id = GCM_REGISTRATION_ID0

    @classmethod
    def groups_create(cls):
        (vendor_group, vendor_group_created) = Group.objects.get_or_create(name='vendor')
        if vendor_group_created:
            vendor_group.save()
        (user_group, user_group_created) = Group.objects.get_or_create(name='user')
        if user_group_created:
            user_group.save()

    @classmethod
    def create(cls, is_active=None, phone_number=None):

        if phone_number != None:
            cls.phone_number = phone_number

        cls.groups_create()

        role = 'user'
        (p0, p0_created) = Profile.get_or_create(phone_number=cls.phone_number,
                role=role, add_registration=False)

        u = p0.user
        if is_active:
            p0.add_user_registration(url_prefix='', raw_password=cls.password, gcm_registration_id=cls.gcm_registration_id)
            ur = UserRegistration.objects.get(user=p0.user)
            ur.activate()

        return u

class _Vendor0(object):
    phone_number = '0987654321'
    username = phone_number
    password = 'u0pw1234'

    @classmethod
    def groups_create(cls):
        (vendor_group, vendor_group_created) = Group.objects.get_or_create(name='vendor')
        if vendor_group_created:
            vendor_group.save()
        (user_group, user_group_created) = Group.objects.get_or_create(name='user')
        if user_group_created:
            user_group.save()

    @classmethod
    def create(cls, restaurant=None):
        cls.groups_create()

        role = 'vendor'
        (p0, p0_created) = Profile.get_or_create(phone_number=cls.phone_number,
                role=role, add_registration=False)

        v = p0.user
        p0.add_user_registration(url_prefix='', raw_password=cls.password, gcm_registration_id=GCM_REGISTRATION_ID1)
        ur = UserRegistration.objects.get(user=p0.user)
        ur.activate()

        p0.restaurant = restaurant
        p0.save()

        return v

def _login_through_api(testcase, username, password):
    return testcase.client.post('/1/login', {'username': username, 'password': password })

class LoginTest(TestCase):
    def test_create_user(self):
        um = get_user_model()
        u0 = _User0.create()
        self.assertEqual(um.objects.get(username=_User0.username).id, u0.id)

    def test_login_success(self):
        u0 = _User0.create(is_active=True)
        res = _login_through_api(self, _User0.username, _User0.password)
        self.assertEqual(res.status_code, 200)

    def test_login_failure(self):
        u0 = _User0.create(is_active=True)
        res = _login_through_api(self, _User0.username, _User0.password + 'XXX')
        self.assertEqual(res.status_code, 401)

class RegisterTest(TestCase):
    def test_bad_requests0(self):
        res = self.client.post('/1/register', {'phone_number': '', 'gcm_registration_id': ''})
        self.assertEqual(res.status_code, 400)

    def test_bad_requests1(self):
        res = self.client.post('/1/register', {'phone_number': _User0.phone_number,
            'password_type': 'raw', 'password': _User0.password, 'gcm_registration_id': ''})
        self.assertEqual(res.status_code, 400)

    def test_wrong_format0(self):
        res = self.client.post('/1/register', {'phone_number': '091112312',  'password_type': 'raw', 'password': '1', 'gcm_registration_id': _User0.gcm_registration_id})
        self.assertEqual(res.status_code, 400)

    def test_wrong_format1(self):
        res = self.client.post('/1/register', {'phone_number': '0911123123',  'password_type': 'raw', 'password': '', 'gcm_registration_id': _User0.gcm_registration_id})
        self.assertEqual(res.status_code, 400)

    def test_success(self):
        api.models.db_init(unit_test_mode=True)
        res = self.client.post('/1/register', {'phone_number': _User0.phone_number,
            'password_type': 'raw', 'password': _User0.password, 'gcm_registration_id': _User0.gcm_registration_id})
        self.assertEqual(res.status_code, 200)
        rs = UserRegistration.objects.filter(user__profile__phone_number=_User0.phone_number)
        assert(len(rs) == 1)

        rs2 = GCMRegistrationId.objects.filter(gcm_registration_id=_User0.gcm_registration_id)
        assert(len(rs2) == 1)
        self.assertEqual(rs2[0].user.username, _User0.username)


    def test_generate_user_registration_message(self):
        pass

class ActivateTest(TestCase):
    def test_not_listed(self):
        res = self.client.get('/1/activate', {'code':'xxx'})
        self.assertEqual(res.status_code, 401)

    def test_success(self):
        u0 = _User0.create()
        m = u0.profile.add_user_registration(url_prefix='', raw_password=_User0.password, gcm_registration_id=_User0.gcm_registration_id)
        start = m.find('/1/activate')
        end = m.find('?code=', start)
        self.assertNotEqual(start, -1)
        self.assertNotEqual(end, -1)
        url = m[start:end]
        (start, end) = ((end + len('?code=')), m.find(' ', start))
        if end == -1:
            code = m[start:]
        else:
            code = m[start:end]
        self.assertEqual(url, '/1/activate')
        res = self.client.get(url, {'code': code})
        self.assertEqual(res.status_code, 200)
        # u0: reload
        u0 = User.objects.get(pk=u0.id)
        self.assertEqual(u0.is_active, True)

class OrderTest(TestCase):

    # post
    def test_no_auth(self):
        self.client.logout()
        res = self.client.post('/1/order_post')
        self.assertEqual(res.status_code, 302)

        u0 = _User0.create()
        r0 = _create_restaurant0();
        res = self.client.post('/1/order_post', {'rest_id': r0.id})
        self.assertEqual(res.status_code, 302)

    def test_wrong_input0(self):
        u0 = _User0.create(is_active=True)
        _login_through_api(self, _User0.username, _User0.password)

        r0 = _create_restaurant0();
        res = self.client.post('/1/order_post', {'rest_id': r0.id})
        self.assertEqual(res.status_code, 400)

    def test_wrong_input1(self):
        u0 = _User0.create(is_active=True)
        _login_through_api(self, _User0.username, _User0.password)

        r0 = _create_restaurant0();
        m0 = _create_meal0()
        res = self.client.post('/1/order_post', {'rest_id': r0.id,
            'order': json.dumps([{'meal_id': m0.id, 'amount': 2}]) + '???',
                })
        self.assertEqual(res.status_code, 400)

    def test_wrong_input2(self):    # empty order
        u0 = _User0.create(is_active=True)
        _login_through_api(self, _User0.username, _User0.password)

        r0 = _create_restaurant0();
        m0 = _create_meal0()
        res = self.client.post('/1/order_post', {'rest_id': r0.id,
            'order': '',
                })
        self.assertEqual(res.status_code, 400)

    def test_different_rest(self):
        u0 = _User0.create(is_active=True)
        _login_through_api(self, _User0.username, _User0.password)

        m0 = _create_meal0()
        m1 = _create_meal0()
        res = self.client.post('/1/order_post', {'order': json.dumps([{'meal_id': m0.id, 'amount': 2}, {'meal_id': m1.id, 'amount': 3}]),
                })
        self.assertEqual(res.status_code, 400)

    def test_success(self):
        u0 = _User0.create(is_active=True)
        _login_through_api(self, _User0.username, _User0.password)

        m0 = _create_meal0()
        jd = json.dumps( [{'meal_id': m0.id, 'amount': 2}] )
        res = self.client.post('/1/order_post', {'order': jd})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, '{"number_slip": 1}')

        o = Order.objects.get()
        res_d = json.loads(res.content)
        self.assertEqual(o.pos_slip_number, res_d['number_slip'])

        oi = o.orderitem_set.get()
        self.assertEqual(oi.meal.id, m0.id)
        self.assertEqual(oi.amount, 2)

    def test_multi_meals_success(self):
        u0 = _User0.create(is_active=True)
        _login_through_api(self, _User0.username, _User0.password)

        m0 = _create_meal0()
        m1 = _create_meal0(create_new_restaurant=False)    #

        res = self.client.post('/1/order_post', {'order': json.dumps([{'meal_id': m0.id, 'amount': 2}, {'meal_id': m1.id, 'amount': 3}]),
                })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, '{"number_slip": 1}')

        o = Order.objects.get()
        oi0 = o.orderitem_set.get(pk=1)
        self.assertEqual(oi0.meal.id, m0.id)
        self.assertEqual(oi0.amount, 2)

        oi1 = o.orderitem_set.get(pk=2)
        self.assertEqual(oi1.meal.id, m1.id)
        self.assertEqual(oi1.amount, 3)

    def test_mutli_orders_success(self):
        u0 = _User0.create(is_active=True)
        _login_through_api(self, _User0.username, _User0.password)

        m0 = _create_meal0()
        jd = json.dumps( [{'meal_id': m0.id, 'amount': 2}] )

        res = self.client.post('/1/order_post', {'order': jd})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, '{"number_slip": 1}')

        o = Order.objects.get()
        oi = o.orderitem_set.get()
        self.assertEqual(oi.meal.id, m0.id)
        self.assertEqual(oi.amount, 2)
        # FIXME: should also check 'number_slip' is set or not

        res = self.client.post('/1/order_post', {'order': jd})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, '{"number_slip": 2}')

    # get
    def test_get_success_empty(self):
        u0 = _User0.create(is_active=True)
        _login_through_api(self, _User0.username, _User0.password)

        res = self.client.get('/1/order_get')
        self.assertEqual(res.status_code, 204)

    def test_get_success(self):
        u0 = _User0.create(is_active=True)
        _login_through_api(self, _User0.username, _User0.password)

        m0 = _create_meal0()
        jd = json.dumps( [{'meal_id': m0.id, 'amount': 2}] )
        self.client.post('/1/order_post', {'order': jd})

        res = self.client.get('/1/order_get')
        self.assertEqual(res.status_code, 200)

        d = json.loads(res.content)

        lo = d['last_order']
        lo['ctime'] = None
        lo['mtime'] = None
        self.assertEqual(lo, {"status": 0, "ctime": None, "restaurant": {u'location': 1, u'name': u'R0', u'rest_id': 1}, "mtime": None, "pos_slip_number": 1})
        oi = d['order_items']
        self.assertEqual(oi, [{"amount": 2, "meal": {u'meal_id': 1, u'meal_name': u'M0', u'meal_price': 100}}])

    def test_multi_order_success(self):
        u0 = _User0.create(is_active=True)
        _login_through_api(self, _User0.username, _User0.password)

        m0 = _create_meal0()
        jd = json.dumps( [{'meal_id': m0.id, 'amount': 2}] )
        self.client.post('/1/order_post', {'order': jd})
        self.client.post('/1/order_post', {'order': jd})

        res = self.client.get('/1/order_get')
        self.assertEqual(res.status_code, 200)

        d = json.loads(res.content)

        lo = d['last_order']
        lo['ctime'] = None
        lo['mtime'] = None

        self.assertEqual(lo, {"status": 0, "ctime": None, "restaurant": {u'location': 1, u'name': u'R0', u'rest_id': 1}, "mtime": None, "pos_slip_number": 2})
        oi = d['order_items']
        self.assertEqual(oi, [{"amount": 2, "meal": {u'meal_id': 1, u'meal_name': u'M0', u'meal_price': 100}}])

def _create_restaurant0():
    r0 = Restaurant(name='R0', location=1)
    r0.save()
    return r0

def _create_meal0(create_new_restaurant=True):
    if create_new_restaurant:
        r0 = _create_restaurant0()
    else:
        r0 = Restaurant.objects.get()
    m0 = Meal(name='M0', price=100, restaurant=r0)
    m0.save()
    return m0

def _create_order0():
    u0 = _User0.create(is_active=True)
    m0 = _create_meal0()
    (o0, ns) = m0.order_create(user=u0, amount=1)
    return o0

def _create_meal_recommendation():
    m0 = _create_meal0()
    u0 = _User0.create(is_active=True)
    mr0 = MealRecommendation(meal=m0, user=u0, description='recommendation description test')
    mr0.save()
    return mr0

class VendorOrderTest(TestCase):
    def test_order_vendor_restaurant_not_set(self):
        r0 = _create_restaurant0()
        v0 = _Vendor0.create(restaurant=r0)

        v0.profile.restaurant = None
        v0.profile.save()

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/order_vendor')
        self.assertEqual(res.status_code, 404)

    def test_order_vendor_empty(self):
        r0 = _create_restaurant0()
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/order_vendor')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.content), [])


    def test_order_vendor(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)

        r0 = o0.restaurant
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/order_vendor')
        self.assertEqual(res.status_code, 200)

        d = json.loads(res.content)
        for i in d:
            i['order']['ctime'] = None
            i['order']['mtime'] = None
        self.assertEqual(d, [{"order": {"status": 0,
                                        "ctime": None,
                                        "restaurant": 1,
                                        "user_comment": "",
                                        "vendor_comment": "",
                                        "user": 1,
                                        "mtime": None,
                                        "pos_slip_number": 1,
                                        "id": 1},
                              "order_items": [{"note": "",
                                               "amount": 1,
                                               "order": 1,
                                               "id": 1,
                                               "meal": 1}]
                              }])

    def test_order_vendor2(self):
        u0 = _User0.create(is_active=True)
        u1 = _User0.create(is_active=True, phone_number=PHONE_NUMBER1)

        m0 = _create_meal0()
        (o0, ns1) = m0.order_create(user=u0, amount=1)
        (o1, ns2) = m0.order_create(user=u0, amount=2)

        r0 = m0.restaurant
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/order_vendor')
        self.assertEqual(res.status_code, 200)

        d = json.loads(res.content)
        for i in d:
            i['order']['ctime'] = None
            i['order']['mtime'] = None
        self.assertEqual(d, [{u'order':
                                {u'status': 0,
                                 u'ctime': None,
                                 u'user_comment': u'',
                                 u'restaurant': 1,
                                 u'id': 1,
                                 u'user': 1,
                                 u'mtime': None,
                                 u'vendor_comment': u'',
                                 u'pos_slip_number': 1},
                              u'order_items': [
                                  {u'note': u'',
                                   u'amount': 1,
                                   u'meal': 1,
                                   u'order': 1,
                                   u'id': 1}]},
                             {u'order':
                                {u'status': 0,
                                 u'ctime': None,
                                 u'user_comment': u'',
                                 u'restaurant': 1,
                                 u'id': 2,
                                 u'user': 1,
                                 u'mtime': None,
                                 u'vendor_comment': u'',
                                 u'pos_slip_number': 2},
                              u'order_items': [
                                  {u'note': u'',
                                   u'amount': 2,
                                   u'meal': 1,
                                   u'order': 2,
                                   u'id': 2}]}])

class PickOrderTest(TestCase):
    def test_order_pick(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)

        r0 = o0.restaurant
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/finish', {'order_key': o0.id})
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/pick', {'order_key': o0.id})
        self.assertEqual(res.status_code, 200)

        o = Order.objects.get(pk=o0.id)
        self.assertEqual(o.status, ORDER_STATUS_PICKED_UP)

    def test_order_pick_from_abondoned(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)

        r0 = o0.restaurant
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        o0.status = ORDER_STATUS_ABANDONED
        o0.save()

        res = self.client.post('/1/pick', {'order_key': o0.id})
        self.assertEqual(res.status_code, 200)

        o = Order.objects.get(pk=o0.id)
        self.assertEqual(o.status, ORDER_STATUS_RESCUED)

    def test_order_pick_without_login(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)

        r0 = o0.restaurant
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/finish', {'order_key': o0.id})
        self.assertEqual(res.status_code, 200)
        self.client.logout()
        res = self.client.post('/1/pick', {'order_key': o0.id})
        self.assertEqual(res.status_code, 302)

        o = Order.objects.get(pk=o0.id)
        self.assertEqual(o.status, ORDER_STATUS_FINISHED)

class FinishOrderTest(TestCase):
    def test_order_finish(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)

        r0 = o0.restaurant
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/finish', {'order_key': o0.id})
        self.assertEqual(res.status_code, 200)

        o = Order.objects.get(pk=o0.id)
        self.assertEqual(o.status, ORDER_STATUS_FINISHED)

        self.assertEqual(o.restaurant.current_number_slip, 1)

    def test_order_finish_without_login(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)

        r0 = o0.restaurant
        v0 = _Vendor0.create(restaurant=r0)

        res = self.client.post('/1/finish', {'order_key': o0.id})
        self.assertEqual(res.status_code, 302)

        o = Order.objects.get(pk=o0.id)
        self.assertEqual(o.status, ORDER_STATUS_INIT_COOKING)

    def test_order_finish_wrong_restaurant(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)

        r0 = _create_restaurant0()
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/finish', {'order_key': o0.id})
        self.assertEqual(res.status_code, 401)

        o = Order.objects.get(pk=o0.id)
        self.assertEqual(o.status, ORDER_STATUS_INIT_COOKING)

    def test_order_finish_current_number_slip_continous0(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)
        (o1, ns) = m0.order_create(user=u0, amount=2)
        (o2, ns) = m0.order_create(user=u0, amount=3)

        r0 = o0.restaurant
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        #
        res = self.client.post('/1/finish', {'order_key': o0.id})
        self.assertEqual(res.status_code, 200)
        o = Order.objects.get(pk=o0.id)
        self.assertEqual(o.status, ORDER_STATUS_FINISHED)
        #
        res = self.client.post('/1/finish', {'order_key': o2.id})
        self.assertEqual(res.status_code, 200)
        o = Order.objects.get(pk=o2.id)
        self.assertEqual(o.status, ORDER_STATUS_FINISHED)

        self.assertEqual(o.restaurant.current_number_slip, 1)

    def test_order_finish_current_number_slip_continous1(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)
        (o1, ns) = m0.order_create(user=u0, amount=2)
        (o2, ns) = m0.order_create(user=u0, amount=3)

        r0 = o0.restaurant
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        #
        res = self.client.post('/1/finish', {'order_key': o0.id})
        self.assertEqual(res.status_code, 200)
        o = Order.objects.get(pk=o0.id)
        self.assertEqual(o.status, ORDER_STATUS_FINISHED)
        #
        res = self.client.post('/1/finish', {'order_key': o2.id})
        self.assertEqual(res.status_code, 200)
        o = Order.objects.get(pk=o2.id)
        self.assertEqual(o.status, ORDER_STATUS_FINISHED)
        #
        res = self.client.post('/1/finish', {'order_key': o1.id})
        self.assertEqual(res.status_code, 200)
        o = Order.objects.get(pk=o1.id)
        self.assertEqual(o.status, ORDER_STATUS_FINISHED)

        self.assertEqual(o.restaurant.current_number_slip, 3)

class CancelOrderTest(TestCase):

    def test_order_cancel(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)

        r0 = o0.restaurant
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/cancel', {'order_key': o0.id})
        self.assertEqual(res.status_code, 200)

        o = Order.objects.get(pk=o0.id)
        self.assertEqual(o.status, ORDER_STATUS_REJECTED)

    def test_order_cancel_without_login(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)

        r0 = o0.restaurant
        v0 = _Vendor0.create(restaurant=r0)

        res = self.client.post('/1/cancel', {'order_key': o0.id})
        self.assertEqual(res.status_code, 302)

        o = Order.objects.get(pk=o0.id)
        self.assertEqual(o.status, ORDER_STATUS_INIT_COOKING)

    def test_order_cancel_wrong_restaurant(self):
        u0 = _User0.create(is_active=True)
        m0 = _create_meal0()
        (o0, ns) = m0.order_create(user=u0, amount=1)

        r0 = _create_restaurant0()
        v0 = _Vendor0.create(restaurant=r0)

        res = _login_through_api(self, _Vendor0.username, _Vendor0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/cancel', {'order_key': o0.id})
        self.assertEqual(res.status_code, 401)

        o = Order.objects.get(pk=o0.id)
        self.assertEqual(o.status, ORDER_STATUS_INIT_COOKING)

class MenuTest(TestCase):
    def test_menu_get(self):
        o0 = _create_order0()
        self.client.logout()
        res = self.client.get('/1/menu')
        self.assertEqual(res.status_code, 400)

        res = self.client.get('/1/menu', {'rest_id':1})
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        self.assertEqual(d, [{u'id': 1, u'price': 100, u'pic_url': u'', u'meal_category': None, u'name': u'M0', u'restaurant': 1, u'status': 0}])

class RestaurantsTest(TestCase):
    def test_restaurant_get(self):
        r0 = _create_restaurant0()
        self.client.logout()
        res = self.client.get('/1/restaurants')
        self.assertEqual(res.status_code, 400)

        res = self.client.get('/1/restaurants', {'location':1})
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        self.assertEqual(d, [{u'capacity': 99, u'current_number_slip': 0, u'id': 1, u'location': 1, u'name': u'R0', u'number_slip': 0, u'pic_url': u'', u'status': 0}])

class OldAPITest(TestCase):
    def test_old_suggestions(self):
        self.client.logout()
        _create_meal_recommendation()
        res = self.client.get('/suggestions.php')
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        self.assertEqual(d,
                         {u'list': [{u'description': u'recommendation description test',
                                     u'name': u'M0',
                                     u'pic_uri': u'',
                                     u'price': u'100',
                                     u'restaurant_name': u'R0'}],
                          u'success': 1})

    def test_old_restaurants(self):
        self.client.logout()
        r0 = _create_restaurant0()
        res = self.client.get('/restaurants.php')
        self.assertEqual(res.status_code, 400)
        res = self.client.get('/restaurants.php', {'location':1})
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        self.assertEqual(d, {u'list': [{u'location': 1,
                                        u'name': u'R0',
                                        u'rest_id': 1}],
                             u'success': 1})

    def test_old_menu(self):
        self.client.logout()
        o0 = _create_order0()
        res = self.client.get('/menu.php', {'rest_id':1})
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        self.assertEqual(d, {u'meal_list': [{u'meal_price': 100,
                                             u'meal_name': u'M0',
                                             u'meal_id': 1}],
                             u'success': 1})

    def test_old_status(self):
        # FIXME: needs response limit, will list all historical orders as written
        self.client.logout()
        o0 = _create_order0()
        res = self.client.post('/status.php')
        self.assertEqual(res.status_code, 400)
        res = self.client.post('/status.php', {'username': _User0.username})
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        # strip time before comparison
        d['list'][0]['time'] = None
        self.assertEqual(d,
                         {u'list': [{u'number_slip': 1,
                                     u'number_slip_index': 1,
                                     u'rest_id': 1,
                                     u'rest_name': u'R0',
                                     u'status': 0,
                                     u'time': None},],
                          u'success': True})

    def test_old_status_detail(self):
        self.client.logout()
        o0 = _create_order0()
        res = self.client.post('/status_detail.php')
        self.assertEqual(res.status_code, 400)
        res = self.client.post('/status_detail.php', {'number_slip_index': o0.id})
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        self.assertEqual(d,
                         {u'list': [{u'amount': 1,
                                     u'meal_id': 1,
                                     u'meal_name': u'M0',
                                     u'meal_price': 100}],
                          u'success': True})

    def test_old_order(self):
        self.client.logout()
        res = self.client.post('/order.php')
        self.assertEqual(res.status_code, 302)

        u0 = _User0.create()
        res = self.client.post('/order.php', {'username': u0.username + 'XXX'})
        self.assertEqual(res.status_code, 302)

        res = self.client.post('/order.php', {'username': u0.username})
        self.assertEqual(res.status_code, 400)

        m0 = _create_meal0()
        res = self.client.post('/order.php', {'username': u0.username,
                                          'rest_id': m0.restaurant.id,
                                          'order': json.dumps([{'meal_id': m0.id, 'amount': 3}]),
                                         })
        self.assertEqual(res.status_code, 200)

        o = Order.objects.get()
        oi = o.orderitem_set.get()
        self.assertEqual(oi.meal.id, m0.id)
        self.assertEqual(oi.amount, 3)

    def test_old_cancel(self):
        self.client.logout()
        res = self.client.post('/cancel.php')
        self.assertEqual(res.status_code, 400)
        res = self.client.post('/cancel.php', {'number_slip_index': 0})
        self.assertEqual(res.status_code, 404)
        o = _create_order0()
        res = self.client.post('/cancel.php', {'number_slip_index': o.id})
        self.assertEqual(res.status_code, 200)
