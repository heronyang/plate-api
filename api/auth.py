from django.conf import settings
from django.contrib.auth.models import User, check_password

from api.models import UserRegistration

class PerDevicePasswordAuthBackend(object):
    """
    A password gets generated every time a user registers
    on a mobile device.
    Allow authenticating with any of the passwords if their marked as
    activated.
    Reference
    https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#authentication-backends
    """

    def authenticate(self, username=None, password=None):
        urs = UserRegistration.objects.filter(user__username=username, clicked=True)
        # FIXME: cache
        for ur in urs:
            if check_password(password, ur.password):
                return ur.user
            if ur.password_type == 'registration_id' and ur.password == password:
                return ur.user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
