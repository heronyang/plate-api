from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

RESTAURANT_NAME_MAX = 33
MEAL_NAME_MAX = 85

# FIXME: https://docs.djangoproject.com/en/dev/ref/contrib/auth/
# django.contrib.auth.User requires a alphanumeric 'username' field

class Profile(models.Model):
    # additional info keyed on User
    user = models.OneToOneField(get_user_model())
    phone_number = models.CharField(max_length=20)
    pic_url = models.URLField(blank=True)
    def __unicode__(self):
        return self.phone_number

class Restaurant(models.Model):
    name = models.CharField(max_length=RESTAURANT_NAME_MAX)
    pic_url = models.URLField(blank=True)
    location = models.IntegerField(default=0) # Enum like
    def __unicode__(self):
        return self.name

class Meal(models.Model):
    name = models.CharField(max_length=MEAL_NAME_MAX)
    pic_url = models.URLField(blank=True)
    price = models.IntegerField()
    restaurant = models.ForeignKey(Restaurant)

    def __unicode__(self):
        return self.name

    def order_create(self, user, amount, time=None, note=None):
        # FIXME: meals could sell out
        if time is None:
            time = timezone.now()
        if note is None:
            note = ''
        order = Order(time=time, user=user, restaurant=self.restaurant)
        order.save()
        oi = OrderItem(meal=self, amount=amount, order=order, note=note)
        oi.save()
        return order

    def order_add(self, amount, order, note=None):
        # FIXME: meals could sell out
        if note is None:
            note = ''
        oi = OrderItem(meal=self, amount=amount, order=order, note=note)
        oi.save()

class Order(models.Model):
    time = models.DateTimeField('time entered')
    user = models.ForeignKey(get_user_model())
    restaurant = models.ForeignKey(Restaurant)
    pos_slip_number = models.IntegerField(blank=True, null=True) # the number printed on the slip by the Point-Of-Sale system
    status = models.IntegerField(default=0)

    def __unicode__(self):
        return '%s %s' % (self.user.email, self.restaurant.name)

    def delete(self):
        # NOTE: consider marking an order as "canceled" instead
        for i in self.orderitem_set.all():
            i.delete()
        super(Order, self).delete()


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
        return '%s %s' % (self.meal.name, self.user.email)
