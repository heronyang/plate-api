"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import json

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from api.models import *

class _User0(object):
    email = 'u0@example.com'
    password = 'u0pw'

    @classmethod
    def create(cls):
        um = get_user_model()
        u0 = um.objects.create_user(cls.email, cls.email, cls.password)
        u0.save()
        return u0

def _login_through_api(testcase, email, password):
    return testcase.client.post('/1/login', {'email': email, 'password': password })

class LoginTest(TestCase):
    def test_create_user(self):
        cls = type(self)
        um = get_user_model()
        u0 = _User0.create()
        self.assertEqual(um.objects.get(email=_User0.email).id, u0.id)

    def test_login_success(self):
        cls = type(self)
        u0 = _User0.create()
        res = _login_through_api(self, _User0.email, _User0.password)
        self.assertEqual(res.status_code, 200)

    def test_login_failure(self):
        cls = type(self)
        u0 = _User0.create()
        res = _login_through_api(self, _User0.email, _User0.password + 'XXX')
        self.assertEqual(res.status_code, 401)

def _create_restaurant0():
    r0 = Restaruant(name='R0', location=1)
    r0.save()
    return r0

def _create_meal0():
    r0 = _create_restaurant0()
    m0 = Meal(name='M0', price=100, restaurant=r0)
    m0.save()
    return m0

def _create_order0():
    u0 = _User0.create()
    m0 = _create_meal0()
    o0 = m0.order_create(user=u0, amount=1)
    return o0

class CancelOrderTest(TestCase):
    def test_order_delete(self):
        o0 = _create_order0()
        o0_id = o0.id
        o0.delete()
        self.assertFalse(OrderItem.objects.filter(order=o0_id))
        self.assertFalse(Order.objects.filter(pk=o0_id))

    def test_order_delete_api(self):
        o0 = _create_order0()
        o0_id = o0.id
        res = _login_through_api(self, _User0.email, _User0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/cancel', {'number_slip_index': o0.id})
        self.assertEqual(res.status_code, 200)
        self.assertFalse(Order.objects.filter(pk=o0_id))

    def test_order_delete_without_login(self):
        self.client.logout()
        o0 = _create_order0()
        o0_id = o0.id
        res = self.client.post('/1/cancel', {'number_slip_index': o0.id})
        self.assertEqual(res.status_code, 401)
        res = _login_through_api(self, _User0.email, _User0.password)
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/1/cancel', {'number_slip_index': o0.id})
        self.assertEqual(res.status_code, 200)

class MenuTest(TestCase):
    def test_menu_get(self):
        o0 = _create_order0()
        self.client.logout()
        res = self.client.get('/1/menu')
        self.assertEqual(res.status_code, 400)

        res = self.client.get('/1/menu', {'rest_id':1})
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        self.assertEqual(d, {u'meal_list': [{u'meal_id': 1, u'meal_name': u'M0', u'meal_price': 100}],
                             u'success': 1})
