from __future__ import absolute_import

import logging
import traceback

from twilio.rest import TwilioRestClient
from twilio import TwilioRestException

from django.core.mail import EmailMessage

from celery import shared_task
from .models import *
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def gcm_send(self, msg, retry_count=0):
    # Pass 'proxies' keyword argument, as described in 'requests' library if you
    # use proxies. Check other options too.
    gcm = GCM(settings.GCM_APIKEY)
    try:
        # attempt send
        res = gcm.send(msg)

        # nothing to do on success
        for reg_id, msg_id in res.success.items():
            logger.info("GCM: Successfully sent %s as %s" % (reg_id, msg_id))

        # update your registration ID's
        for reg_id, new_reg_id in res.canonical.items():
            logger.info("GCM: Replacing %s with %s in database" % (reg_id, new_reg_id))
            gs = GCMRegistrationId.objects.filter(gcm_registration_id=reg_id)
            for g in gs:
                g.gcm_registration_id=new_reg_id
                g.save()

        # probably app was uninstalled
        for reg_id in res.not_registered:
            logger.info("GCM: Removing %s from database" % reg_id)
            gs = GCMRegistrationId.objects.filter(gcm_registration_id=reg_id)
            for g in gs:
                g.delete()
                g.save()

        # unrecoverably failed, these ID's will not be retried
        # consult GCM manual for all error codes
        for reg_id, err_code in res.failed.items():
            logger.info("GCM: Removing %s because %s" % (reg_id, err_code))

        # if some registration ID's have recoverably failed
        if res.needs_retry():
            retry_count = getattr(self, 'retry_count', 0)
            self.retry_count = retry_count + 1
            self.apply_async((res.retry(), retry_count + 1), countdown=res.delay(retry_count))
    except GCMAuthenticationError:
        # stop and fix your settings
        logger.error("GCM: Your Google API key is rejected")
        raise
    except ValueError, e:
        # probably your extra options, such as time_to_live,
        # are invalid. Read error message for more info.
        logger.error("GCM: Invalid message/option or invalid GCM response\t" + e.args[0])
        raise
    except Exception:
        # your network is down or maybe proxy settings
        # are broken. when problem is resolved, you can
        # retry the whole message.
        logger.error('GCM: Exception: ' + traceback.format_exc())
        raise

@shared_task
def order_status_daily_cleanup():
    Order.daily_cleanup()

@shared_task
def sms_send(international_phone_number, msg):
    client = TwilioRestClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    try:
        sms = client.sms.messages.create(body=msg,
                                         to=international_phone_number,
                                         from_=settings.TWILIO_PHONE_NUMBER)
    except TwilioRestException as e:
        logger.error('SMS: TwilioRestException, code: ' + str(e.code))
        # error code reference: https://www.twilio.com/docs/errors/reference
        raise

@shared_task
def email_admin(title, msg):
    email_list = []
    for e in settings.ADMINS:
        email_list.append(e[1])
    email = EmailMessage(title, msg, to=email_list)
    email.send()
