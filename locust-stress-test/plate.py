#!/usr/bin/env python

# API Reference: http://docs.locust.io/en/latest/api.html#locust.clients.HttpSession.get

import random
from locust import HttpLocust, TaskSet, task

MIN_WAIT = 5000
MAX_WAIT = 15000

def phone_number_gen():
    '-> 09xx xxx xxx'
    return '09' + ''.join( chr(ord('0') + random.randrange(10)) for x in range(8) )

class UnregisteredPlateUserTasks(TaskSet):
    #tasks = {user_register:1, restaurant_get:5, menu_get:5}

    def on_start(self):
        # login etc
        pass

    @task
    def user_register(self):
        d = dict(phone_number=phone_number_gen(),
                 password='X' * 20,
                 password_type='raw',
                 gcm_registration_id='FAKE-GCM-REGISTRATION-ID')
        r = self.client.post('/1/register', d)
        #assert (r.status == 200)

    @task
    def restaurant_get(self):
        r = self.client.get('/restaurants.php', params={'location': 0})

    @task
    def menu_get(self):
        r = self.client.get('/menu.php', params={'rest_id': 1})


class RegisteredPlateUserTasks(TaskSet):

    username = '0900111222'
    password = 'lSaydmnFjA8ZX'

    def on_start(self):
        self.client.post('/1/login', {'username': self.username, 'password': self.password })

    @task
    def order_post(self):
        pass

class PlateVendorTasks(TaskSet):

    vendor_username = 'v1'
    vendor_password = 'platerocks'

    def on_start(self):
        self.client.post('/1/login', {'username': self.vendor_username, 'password': self.vendor_password })

    @task
    def order_get(self):
        r1 = self.client.post('/1/order_vendor')
        r2 = self.client.get('/1/restaurant_status')

class UnregisteredPlateUser(HttpLocust):
    task_set = UnregisteredPlateUserTasks
    weight = 150
    min_wait = MIN_WAIT
    max_wait = MAX_WAIT

class RegisteredPlateUser(HttpLocust):
    task_set = RegisteredPlateUserTasks
    weight = 150
    min_wait = MIN_WAIT
    max_wait = MAX_WAIT

class PlateVendor(HttpLocust):
    task_set = PlateVendorTasks
    weight = 8
    min_wait = MIN_WAIT
    max_wait = MAX_WAIT
