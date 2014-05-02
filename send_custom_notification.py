#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plate_server.settings")
from api.models import *

if __name__ == "__main__":

    title = 'Thanks for using PLATE'
    message = '感謝您使用PLATE點餐系統'
    method = 'gcm'  # gcm or sms

    us = User.objects.all()
    for u in us:
        if re.match(r'^09(\d{8})$', u.username):
            if u.username == '0983345113':
                u.profile.send_custom_notification(title, message, method)
                print u.username + ' is added to task queue'
