#!/usr/bin/env python

# URL = 'https://api.plate.tw'
URL = 'http://127.0.0.1:8000'

import random
import urllib
import urlparse
import httplib

def phone_number_gen():
    '-> 09xx xxx xxx'
    return '09' + ''.join( chr(ord('0') + random.randrange(10)) for x in range(8) )

class Transaction(object):
    def run(self):
        d = dict(phone_number=phone_number_gen(),
                 password='X' * 20,
                 password_type='raw',
                 gcm_registration_id='FAKE-GCM-REGISTRATION-ID')
        body = urllib.urlencode(d)
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        t = urlparse.urlparse(URL)
        if t.scheme == 'http':
            conn = httplib.HTTPConnection(URL[len(t.scheme)+len('://'): ])
        elif t.scheme == 'https':
            conn = httplib.HTTPSConnection(URL[len(t.scheme)+len('://'): ])
        else:
            assert(0)
        conn.request('POST', '/1/register', body, headers)
        res = conn.getresponse()
        res_body = res.read()
        assert (res.status == 200)

if __name__ == '__main__':
    txn = Transaction()
    txn.run()
