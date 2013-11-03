from django.conf.urls import patterns, include, url

from api import views

urlpatterns = patterns('',
    url(r'^1/register$', views.register, name='register'),
    url(r'^1/login$', views.login, name='login'),
    url(r'^1/cancel$', views.cancel, name='cancel'),
    url(r'^1/menu$', views.menu, name='menu'),
    url(r'^1/order$', views.order, name='order'),
    url(r'^1/restaurants$', views.restaurants, name='restaurants'),
    url(r'^1/status-details$', views.status_details, name='status_details'),
    url(r'^1/status$', views.status, name='status'),
    url(r'^1/recommendations$', views.recommendations, name='recommendations'),

    url(r'^suggestions.php$', views.old_suggestions, name='menu'),
    url(r'^menu.php$', views.old_menu, name='menu'),
    url(r'^restaurants.php$', views.old_restaurants, name='old_restaurants'),
)
