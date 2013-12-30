import json

from django.http import HttpResponse
from django.contrib.auth import authenticate
import django.contrib.auth
import django.core
from django.views.decorators.csrf import csrf_exempt
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_GET, require_POST, require_http_methods
import django.views.generic.base
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
import re

from jsonate import jsonate

from api.models import *

CONTENT_TYPE_JSON = 'application/json'
CONTENT_TYPE_TEXT = 'text/plain'

def is_user(user):
    return user.groups.filter(name='user')

def is_vendor(vendor):
    return vendor.groups.filter(name='vendor')

@csrf_exempt
@require_GET
def vendor_list(request):
    res = HttpResponse(content_type=CONTENT_TYPE_JSON)

    group = Group.objects.get(name='vendor')
    users = group.user_set.all()

    vendor_usernames = []
    for i in users:
        vendor_usernames.append(i.username)

    res.status_code = 200
    res.content = jsonate({'vendor_usernames':vendor_usernames})
    return res

@csrf_exempt
@require_POST
def register(request):
    #FIXME: add password type, if raw is using un-decode ones
    res = HttpResponse(content_type=CONTENT_TYPE_JSON)
    try:
        phone_number = request.POST['phone_number']
        password = request.POST['password']
        password_type = request.POST['password_type']
        gcm_registration_id = request.POST['gcm_registration_id']
    except MultiValueDictKeyError:
        res.status_code = 400
        return res

    if (not phone_number) or (not gcm_registration_id):
        res.status_code = 400   # wrong input
        return res

    if not is_valid_password(password):
        res.status_code = 400   # wrong input
        return res

    if password_type == 'raw':
        h = PBKDF2PasswordHasher()
        password = h.encode(password, h.salt())
    elif password_type == 'encoded':
        pass
        #FIXME: verify encoded_password is a 3 part hash
        # (algo, salt, encoded)
    else:
        res.status_code = 400
        return res

    (profile, profile_created) = Profile.get_or_create(phone_number=phone_number, role='user')

    url_prefix = request.build_absolute_uri()[:-len(request.get_full_path())]
    wsgi_mount_point = request.path[:-len(request.path_info)]
    if wsgi_mount_point:
         url_prefix += wsgi_mount_point

    m = profile.add_user_registration(url_prefix, password=password, gcm_registration_id=gcm_registration_id)
    c = Configuration.get0()
    if not c.unit_test_mode:
        profile.__send_verification_message(m)

    res.status_code = 200
    return res

@csrf_exempt
@require_GET
def activate(request):
    res = HttpResponse(content_type=CONTENT_TYPE_TEXT)

    #FIXME: check if the record is clicked
    code = request.GET['code']
    try:
        ur = UserRegistration.objects.get(code=code)
    except UserRegistration.DoesNotExist:
        res.status_code = 401
        return res

    if ur.clicked:
        res.status_code = 203
        res.content = 'Already clicked'
    else:
        try:
            ur.activate()
        except IntegrityError, e:
            res = status = 400
            res.content = e.args[0]
            return res

        res.status_code = 200
        res.content = 'Success!'
    return res

@csrf_exempt
@require_POST
def login(request):
    res = HttpResponse(content_type=CONTENT_TYPE_JSON)
    (username, password) = (request.POST['username'], request.POST['password'])
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            django.contrib.auth.login(request, user)
            res.status_code = 200
        else:
            res.status_code = 401 # unauthorized
    else:
        res.status_code = 401 # unauthorized
    return res


@csrf_exempt
@require_GET
def menu(request):
    res = HttpResponse(content_type=CONTENT_TYPE_JSON)
    try:
        restaurant_key = request.GET['rest_id']
    except MultiValueDictKeyError:
        res.status_code = 400
        return res

    res.status_code = 200
    res.content = jsonate(Meal.objects.filter(restaurant=restaurant_key))
    return res

@csrf_exempt
@require_POST
@login_required
@user_passes_test(is_user)
def order_post(request):
    res = HttpResponse(content_type=CONTENT_TYPE_TEXT)
    user = request.user

    # create new order
    # FIXME: should check 'can_place_order'

    try:
        order_json = request.POST['order']
    except MultiValueDictKeyError:
        res.content = "post error"
        res.status_code = 400
        return res

    try:
        order_data = json.loads(order_json)
    except ValueError:
        res.content = "json parsing error"
        res.status_code = 400
        return res

    if not order_data:
        res.content = "empty order"
        res.status_code = 400
        return res

    # check if all meals are from the same restaurant
    m = order_data[0]['meal_id']
    rest = Meal.objects.get(pk=m).restaurant

    for i in order_data[1:]:
        m = i['meal_id']
        if rest.id != Meal.objects.get(pk=m).restaurant.id:
            res.content = "must be in the same restaurant"
            res.status_code = 400
            return res

    # FIXME: does it make more sense to implement 'order_create' at Restuarant?
    i = order_data[0]
    (meal_key, amount) = (i['meal_id'], i['amount'])
    (order, number_slip) = Meal.objects.get(pk=meal_key).order_create(user=user, amount=amount)

    for i in order_data[1:]:
        (meal_key, amount) = (i['meal_id'], i['amount'])
        Meal.objects.get(pk=meal_key).order_add(amount=amount, order=order)

    res.content = jsonate(dict(number_slip = number_slip))
    res.status_code = 200
    return res

@csrf_exempt
@require_GET
@login_required
@user_passes_test(is_user)
def order_get(request):
    # list eixsting order (only the latest one)
    res = HttpResponse(content_type=CONTENT_TYPE_TEXT)

    user = request.user
    orders = Order.objects.filter(user=user).order_by('-ctime')

    if not orders:
        res.content = "no processing order"
        res.status_code = 204
        return res

    last_order = orders[:1][0]

    # last_order
    r_d = dict(name = last_order.restaurant.name,
               location = last_order.restaurant.location,
               rest_id = last_order.restaurant.id)
    l_d = dict(ctime = last_order.ctime,
               mtime = last_order.mtime,
               restaurant = r_d,
               pos_slip_number = last_order.pos_slip_number,
               status = last_order.status)

    # order_items
    order_items = OrderItem.objects.filter(order=last_order)
    l_l = []
    for i in order_items:
        m_d = dict(meal_name = i.meal.name,
                   meal_price = i.meal.price,
                   meal_id = i.meal.id)
        l_l.append(dict(meal = m_d, amount = i.amount))

    # combine, and output
    receipt = {}
    receipt['last_order'] = l_d
    receipt['order_items'] = l_l

    res.content = jsonate(receipt)
    res.status_code = 200
    return res

class OrderView(django.views.generic.base.View):

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        res = HttpResponse(content_type=CONTENT_TYPE_TEXT)
        user = request.user

        # create new order
        # FIXME: should check 'can_place_order'

        try:
            order_json = request.POST['order']
        except MultiValueDictKeyError:
            res.content = "post error"
            res.status_code = 400
            return res

        try:
            order_data = json.loads(order_json)
        except ValueError:
            res.content = "json parsing error"
            res.status_code = 400
            return res

        if not order_data:
            res.content = "empty order"
            res.status_code = 400
            return res

        # check if all meals are from the same restaurant
        m = order_data[0]['meal_id']
        rest = Meal.objects.get(pk=m).restaurant

        for i in order_data[1:]:
            m = i['meal_id']
            if rest.id != Meal.objects.get(pk=m).restaurant.id:
                res.content = "must be in the same restaurant"
                res.status_code = 400
                return res

        # FIXME: does it make more sense to implement 'order_create' at Restuarant?
        i = order_data[0]
        (meal_key, amount) = (i['meal_id'], i['amount'])
        (order, number_slip) = Meal.objects.get(pk=meal_key).order_create(user=user, amount=amount)

        for i in order_data[1:]:
            (meal_key, amount) = (i['meal_id'], i['amount'])
            Meal.objects.get(pk=meal_key).order_add(amount=amount, order=order)

        res.content = jsonate(dict(number_slip = number_slip))
        res.status_code = 200
        return res


    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        # list eixsting order (only the latest one)
        res = HttpResponse(content_type=CONTENT_TYPE_TEXT)

        user = request.user
        orders = Order.objects.filter(user=user).order_by('-ctime')

        if not orders:
            res.content = "no processing order"
            res.status_code = 204
            return res

        last_order = orders[:1][0]

        # last_order
        r_d = dict(name = last_order.restaurant.name,
                   location = last_order.restaurant.location,
                   rest_id = last_order.restaurant.id)
        l_d = dict(ctime = last_order.ctime,
                   mtime = last_order.mtime,
                   restaurant = r_d,
                   pos_slip_number = last_order.pos_slip_number,
                   status = last_order.status)

        # order_items
        order_items = OrderItem.objects.filter(order=last_order)
        l_l = []
        for i in order_items:
            m_d = dict(meal_name = i.meal.name,
                       meal_price = i.meal.price,
                       meal_id = i.meal.id)
            l_l.append(dict(meal = m_d, amount = i.amount))

        # combine, and output
        receipt = {}
        receipt['last_order'] = l_d
        receipt['order_items'] = l_l

        res.content = jsonate(receipt)
        res.status_code = 200
        return res

@csrf_exempt
@require_GET
def current_ns(require):
    res = HttpResponse(content_type=CONTENT_TYPE_JSON)

    try:
        rest_id = require.GET['rest_id']
    except MultiValueDictKeyError:
        res.status_code = 400
        return res

    r = Restaurant.objects.get(pk=rest_id)

    res.status_code = 200
    res.content = jsonate({'current_ns': r.current_number_slip})
    return res

@csrf_exempt
@require_GET
def restaurants(request):
    res = HttpResponse(content_type=CONTENT_TYPE_JSON)
    try:
        location_key = request.GET['location']
    except MultiValueDictKeyError:
        res.status_code = 400
        return res
    res.status_code = 200
    res.content = jsonate(Restaurant.objects.filter(location=location_key))
    return res

@csrf_exempt
@require_POST
@login_required
@user_passes_test(is_vendor)
def order_vendor(request):
    res = HttpResponse(content_type=CONTENT_TYPE_TEXT)
    vendor = request.user
    restaurant = vendor.profile.restaurant

    if not restaurant:
        res.content = "the restaurant of this vendor is not set"
        res.status_code = 400
        return res

    orders = Order.objects.filter(restaurant = restaurant)
    r = []
    for i in orders:
        row = {}
        row['order'] = i

        u = i.user
        row['user'] = dict(username=u.username,
                           first_name=u.first_name,
                           last_name=u.last_name,
                           email=u.email,
                           id=u.id)


        order_items = OrderItem.objects.filter(order=i)
        oi_packed = []
        for j in order_items:
            oi = {}
            m = j.meal
            oi['meal'] = dict(meal_price=m.price,
                              meal_name=m.name,
                              meal_id=m.id)
            oi['amount'] = j.amount
            oi_packed.append(oi)

        row['order_items'] = oi_packed
        r.append(row)

    res.status_code = 200
    res.content = jsonate(dict(orders=r))
    return res


@csrf_exempt
@require_POST
@login_required
@user_passes_test(is_vendor)
def finish(request):
    res = HttpResponse(content_type=CONTENT_TYPE_TEXT)
    vendor = request.user

    if not vendor.is_authenticated():
        res.status_code = 401
        return res

    order_key = request.POST['order_key']

    try:
        o = Order.objects.get(pk=order_key)
    except Order.DoesNotExist:
        res.status_code = 404
        return res

    #
    if o.restaurant != vendor.profile.restaurant:
        res.content = "this is not your restaurant's order"
        res.status_code = 401
        return res

    r = o.finish()
    if not r:
        res.content = "not able to cancel in this state"
        res.status_code = 406   # Not Acceptable
        return res

    res.status_code = 200
    return res

@csrf_exempt
@require_POST
@login_required
@user_passes_test(is_vendor)
def pickup(request):
    res = HttpResponse(content_type=CONTENT_TYPE_TEXT)
    vendor = request.user

    if not vendor.is_authenticated():
        res.status_code = 401
        return res

    order_key = request.POST['order_key']

    try:
        o = Order.objects.get(pk=order_key)
    except Order.DoesNotExist:
        res.status_code = 404
        return res

    #
    if o.restaurant != vendor.profile.restaurant:
        res.content = "this is not your restaurant's order"
        res.status_code = 401
        return res

    # success
    r = o.pickup()
    if not r:
        res.content = "not able change to finish state from this state"
        res.status_code = 406   # Not Acceptable
        return res

    res.status_code = 200
    return res

@csrf_exempt
@require_POST
@login_required
@user_passes_test(is_vendor)
def cancel(request):
    res = HttpResponse(content_type=CONTENT_TYPE_TEXT)
    vendor = request.user

    if not vendor.is_authenticated():
        res.status_code = 401
        return res

    order_key = request.POST['order_key']

    try:
        o = Order.objects.get(pk=order_key)
    except Order.DoesNotExist:
        res.status_code = 404
        return res

    #
    if o.restaurant != vendor.profile.restaurant:
        res.content = "this is not your restaurant's order"
        res.status_code = 401
        return res

    r = o.cancel()
    if not r:
        res.content = "not able to cancel in this state"
        res.status_code = 406   # Not Acceptable
        return res

    res.status_code = 200
    return res

###

@csrf_exempt
@require_GET
@login_required
def user_orders(request):
    assert(0)

@csrf_exempt
@require_GET
@login_required
def recommendations(request):
    assert(0)


# FIXME: turn off old APIs before release, so 'cancel' won't make any mistake

@csrf_exempt
@require_GET
def old_suggestions(request):
    res = HttpResponse(content_type=CONTENT_TYPE_JSON)
    mrs = MealRecommendation.objects.all()
    out = {}
    if mrs:
        out['success'] = 1
    else:
        out['success'] = 0

    l = []
    for i in mrs:
        l.append(dict(name=i.meal.name,
                      restaurant_name=i.meal.restaurant.name,
                      pic_uri=i.meal.pic_url,
                      description=i.description,
                      price=str(i.meal.price)))
    out['list'] = l
    res.content = json.dumps(out)
    res.status_code = 200
    return res

@csrf_exempt
@require_GET
def old_restaurants(request):
    res = HttpResponse(content_type=CONTENT_TYPE_JSON)
    try:
        location = request.GET['location']
    except MultiValueDictKeyError:
        res.status_code = 400
        return res

    out = {}
    rs = Restaurant.objects.filter(location=location)
    if rs:
        out['success'] = 1
    else:
        out['success'] = 0

    l = []
    for i in rs :
        l.append(dict(name=i.name, location=i.location, rest_id=i.id))
    out['list'] = l
    res.content = json.dumps(out)
    res.status_code = 200
    return res

@csrf_exempt
@require_GET
def old_menu(request):
    res = HttpResponse(content_type=CONTENT_TYPE_JSON)
    try:
        restaurant_key = request.GET['rest_id']
    except MultiValueDictKeyError:
        res.status_code = 400
        res.content = 'empty rest_id'
        return res

    ms = Meal.objects.filter(restaurant=restaurant_key)
    out = {}
    if not ms:
        out['success'] = 0
    else:
        out['success'] = 1

    meal_list = []
    for i in ms:
        meal_list.append(dict(meal_id=i.id, meal_name=i.name, meal_price=i.price))
    out['meal_list'] = meal_list

    res.status_code = 200
    res.content = json.dumps(out)
    return res

@csrf_exempt
@require_POST
def old_status(request):
    # List orders for a user in reverse chronologically
    res = HttpResponse(content_type=CONTENT_TYPE_JSON)
    try:
        username = request.POST['username']
    except MultiValueDictKeyError:
        res.status_code = 400
        res.content = json.dumps({'error': 'missing username'})
        return res

    orders = Order.objects.filter(user__username=username).order_by('-ctime')
    out = {}
    if orders:
        out['success'] = True
    else:
        out['success'] = False
    l = []
    for i in orders:
        oi = i.orderitem_set.all()[0]
        restaurant = oi.meal.restaurant
        l.append(dict(time=i.ctime,
                      number_slip_index=i.id,
                      number_slip=i.pos_slip_number,
                      rest_id=restaurant.id,
                      rest_name=restaurant.name,
                      status=i.status))
    out['list'] = l
    res.status_code = 200
    res.content = jsonate(out)
    return res

@csrf_exempt
@require_POST
def old_status_detail(request):
    res = HttpResponse(content_type=CONTENT_TYPE_JSON)
    try:
        order_key = request.POST['number_slip_index']
    except MultiValueDictKeyError:
        res.status_code = 400
        return res

    # Using order_by('id') to keep the OrderItem's in the same order
    # in old_status_detail() and old_order()
    order_items = Order.objects.get(pk=order_key).orderitem_set.all().order_by('id')
    out =  {}
    if order_items:
        out['success'] = True
    else:
        out['success'] = False

    l = []
    for i in order_items:
        meal = i.meal
        l.append(dict(amount=i.amount,
                      meal_id=meal.id,
                      meal_name=meal.name,
                      meal_price=meal.price))
    out['list'] = l
    res.status_code = 200
    res.content = jsonate(out)
    return res

@csrf_exempt
@require_POST
def old_order(request):
    res = HttpResponse(content_type=CONTENT_TYPE_TEXT)
    try:
        username = request.POST['username']
    except MultiValueDictKeyError:
        res.status_code = 302
        return res
    try:
        user = get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist:
        res.status_code = 302
        return res

    try:
        restaurant_key = request.POST['rest_id']
        order_data = request.POST['order']
    except MultiValueDictKeyError:
        res.status_code = 400
        return res

    try:
        order_data = json.loads(order_data)
    except ValueError:
        res.status_code = 400
        return res

    if not order_data:
        res.status_code = 200
        return res

    i = order_data[0]
    (meal_key, amount) = (i['meal_id'], i['amount'])
    order = Meal.objects.get(pk=meal_key).order_create(user=user, amount=amount)

    for i in order_data[1:]:
        (meal_key, amount) = (i['meal_id'], i['amount'])
        Meal.objects.get(pk=meal_key).order_add(amount=amount, order=order, note='app push')
    res.status_code = 200
    return res

@csrf_exempt
@require_POST
def old_cancel(request):
    res = HttpResponse(content_type=CONTENT_TYPE_TEXT)
    try:
        order_key = request.POST['number_slip_index']
    except MultiValueDictKeyError:
        res.status_code = 400
        return res

    # The Order model will delete related OrderItem's as well
    # Still, deleting rows instead of marking them as canceled is very weird
    try:
        Order.objects.get(pk=order_key).delete()
    except Order.DoesNotExist:
        res.status_code = 404
    else:
        res.status_code = 200
    return res
