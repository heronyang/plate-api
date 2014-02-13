#!/usr/bin/env python

# API Reference: http://docs.locust.io/en/latest/api.html#locust.clients.HttpSession.get

import random
from locust import HttpLocust, TaskSet, task

def phone_number_gen():
    '-> 09xx xxx xxx'
    return '09' + ''.join( chr(ord('0') + random.randrange(10)) for x in range(8) )

class PlateTasks(TaskSet):
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
    def menu_get(self):
        r = self.client.get('/menu.php', params={'rest_id': 1})

class PlateUser(HttpLocust):
    task_set = PlateTasks
    main_wait = 5000
    max_wait = 15000
