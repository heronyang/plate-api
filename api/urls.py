from django.conf.urls import patterns, include, url

from api import views

urlpatterns = patterns('',
    url(r'^1/register$', views.register, name='register'),
    url(r'^1/login$', views.login, name='login'),
    url(r'^1/cancel$', views.cancel, name='cancel'),
    url(r'^1/menu$', views.menu, name='menu'),
    url(r'^1/order$', views.OrderView.as_view(), name='order'),
    url(r'^1/restaurants$', views.restaurants, name='restaurants'),
    url(r'^1/user-orders$', views.user_orders, name='user_orders'),
    url(r'^1/recommendations$', views.recommendations, name='recommendations'),
    url(r'^1/activate$', views.activate, name='activate'),

    # Old API
    url(r'^suggestions.php$', views.old_suggestions, name='old_suggestions'),
    url(r'^restaurants.php$', views.old_restaurants, name='old_restaurants'),
    url(r'^menu.php$', views.old_menu, name='old_menu'),
    url(r'^status.php$', views.old_status, name='old_status'),
    url(r'^status_detail.php$', views.old_status_detail, name='old_status_detail'),
    url(r'^order.php$', views.old_order, name='old_order'),
    url(r'^cancel.php$', views.old_cancel, name='old_cancel'),
)
