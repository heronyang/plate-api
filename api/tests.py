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

def _create_meal_recommendation():
    m0 = _create_meal0()
    u0 = _User0.create()
    mr0 = MealRecommendation(meal=m0, user=u0, description='recommendation description test')
    mr0.save()
    return mr0

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
        self.assertEqual(res.status_code, 302)
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
        self.assertEqual(d, [{u'id': 1, u'price': 100, u'pic_url': u'', u'name': u'M0', u'restaurant': 1}])

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
        self.client.logout()
        o0 = _create_order0()
        res = self.client.post('/status.php')
        self.assertEqual(res.status_code, 400)
        res = self.client.post('/status.php', {'username': _User0.email})
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        # strip time before comparison
        d['list'][0]['time'] = None
        self.assertEqual(d,
                         {u'list': [{u'number_slip': None,
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
