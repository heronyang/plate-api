from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from api.models import *
from pytz import timezone

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profiles'

class MyUserAdmin(UserAdmin):
    # FIXME: show pic_url as avatar
    inlines = [ProfileInline]
    list_display = ('username', 'phone_number', 'last_name', 'first_name', 'email', 'is_active', 'failure', 'restaurant')

    def phone_number(self, user):
        return user.profile.phone_number

    def failure(self, user):
        return user.profile.failure
    # vendor
    def restaurant(self, user):
        return user.profile.restaurant

class RestaurantAdmin(admin.ModelAdmin):
    # FIXME: symbolic names for 'location'
    list_display = ('name', 'pic_tag', 'location', 'number_slip', 'current_number_slip', 'status', 'description')
    search_fields = ['name']
    list_filter = ['location']

    def location(self):
        return self.location.name

class MealAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'name', 'price', 'status', 'pic_tag', 'pic_url', 'meal_category')

    search_fields = ['name', 'restaurant__name']
    list_filter = ['restaurant__name']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ('ctime', 'mtime', 'username', 'restaurant', 'pos_slip_number', 'status', 'user_comment', 'vendor_comment')

    def username(self, order):
        return order.user.username

    search_fields = ['user__email', 'restaurant__name']
    list_filter = ['restaurant']
    #date_hierarchy = 'ctime'

class MealRecommendationsAdmin(admin.ModelAdmin):
    list_display = ('username', 'restaurant_name', 'meal_name')

    def username(self, recommendation):
        return recommendation.user.username

    def restaurant_name(self, recommendation):
        return recommendation.meal.restaurant.name

    def meal_name(self, recommendation):
        return recommendation.meal.name

    search_fields = ['user__email', 'meal__name']
    list_filter = ['user']

class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'timezone')

class ClosedReasonAdmin(admin.ModelAdmin):
    list_display = ('msg',)

class UserRegistrationAdmin(admin.ModelAdmin):
    list_display = ('username', 'code', 'ctime', 'clicked')

    def username(self, user_registration):
        return user_registration.user.username

class GCMRegistrationIdAdmin(admin.ModelAdmin):
    list_display = ('user', 'gcm_registration_id')

class LastRegistrationTimeAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_time')

class VendorLastRequestTimeAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'last_time')

class RestaurantHolidayAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'closed_date')

class RestaurantOpenHoursAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'start', 'end')

class OrderStatusChangeTimeAdmin(admin.ModelAdmin):
    list_display = ('username', 'order_rest', 'ctime', 'finish_time', 'pickup_time')
    def username(self, ct):
        return ct.order.user.username
    def order_rest(self, ct):
        return ct.order.restaurant.name

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), MyUserAdmin)
admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Meal, MealAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(MealRecommendation, MealRecommendationsAdmin)
admin.site.register(UserRegistration, UserRegistrationAdmin)
admin.site.register(MealCategory)
admin.site.register(GCMRegistrationId, GCMRegistrationIdAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(ClosedReason, ClosedReasonAdmin)
admin.site.register(VendorLastRequestTime, VendorLastRequestTimeAdmin)
admin.site.register(LastRegistrationTime, LastRegistrationTimeAdmin)
admin.site.register(RestaurantHoliday, RestaurantHolidayAdmin)
admin.site.register(RestaurantOpenHours, RestaurantOpenHoursAdmin)
admin.site.register(OrderStatusChangeTime, OrderStatusChangeTimeAdmin)
