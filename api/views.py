import json

from django.http import HttpResponse
from django.contrib.auth import authenticate
import django.contrib.auth
from django.views.decorators.csrf import csrf_exempt
from django.utils.datastructures import MultiValueDictKeyError

from api.models import *

@csrf_exempt
def register(request):
    assert(0)

@csrf_exempt
def login(request):
    res = HttpResponse()
    if request.method != 'POST':
        res.status_code = 400 # bad request
        return res

    (email, password) = (request.POST['email'], request.POST['password'])
    user = authenticate(username=email, password=password)
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
def cancel(request):
    res = HttpResponse()
    if request.method != 'POST':
        res.status_code = 400 # bad request
        return res

    user = request.user
    # FIXME: should check "ordered_by_user or is_order_vendor or is_superuser"
    if not user.is_authenticated():
        res.status_code = 401
        return res

    order_key = request.POST['number_slip_index']
    # FIXME: mark orders as canceled, don't delete them
    try:
        o = Order.objects.get(pk=order_key)
    except Order.DoesNotExist:
        res.status_code = 404
    else:
        o.delete()
        res.status_code = 200
    return res

@csrf_exempt
def menu(request):
    pass

@csrf_exempt
def order(request):
    res = HttpResponse()
    if request.method != 'POST':
        res.status_code = 400 # bad request
        return res

    user = request.user
    # FIXME: should check 'can_place_order'
    if not user.is_authenticated():
        res.status_code = 401
        return res

    restaurant_key = request.POST['rest_id']


@csrf_exempt
def restaurants(request):
    assert(0)

@csrf_exempt
def status_details(request):
    assert(0)

@csrf_exempt
def status(request):
    assert(0)

@csrf_exempt
def recommendations(request):
    assert(0)

@csrf_exempt
def old_suggestions(request):
    res = HttpResponse(content_type='application/json')
    if request.method != 'GET':
        res.status_code = 400 # bad request
        return res

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
def old_restaurants(request):
    res = HttpResponse(content_type='application/json')
    if request.method != 'GET':
        res.status_code = 400 # bad request
        return res
    try:
        location = request.GET['location']
    except MultiValueDictKeyError:
        res.status_code = 400
        return res

    out = {}
    rs = Restaruant.objects.filter(location=location)
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
def old_menu(request):
    res = HttpResponse(content_type='application/json')
    if request.method != 'GET':
        res.status_code = 400 # bad request
        return res

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
