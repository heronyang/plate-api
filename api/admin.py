from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from api.models import *

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profiles'

class MyUserAdmin(UserAdmin):
    # FIXME: show pic_url as avatar
    inlines = [ProfileInline]
    list_display = ('username', 'phone_number', 'last_name', 'first_name', 'email', 'is_active', 'restaurant')

    def phone_number(self, user):
        return user.profile.phone_number

    # vendor
    def restaurant(self, user):
        return user.profile.restaurant

class RestaurantAdmin(admin.ModelAdmin):
    # FIXME: symbolic names for 'location'
    list_display = ('name', 'pic_tag', 'location_name', 'number_slip', 'current_number_slip')
    search_fields = ['name']
    list_filter = ['location']

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

class UserRegistrationAdmin(admin.ModelAdmin):
    list_display = ('username', 'code', 'ctime', 'clicked', 'password', 'password_type')

    def username(self, user_registration):
        return user_registration.user.username

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), MyUserAdmin)
admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Meal, MealAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(MealRecommendation, MealRecommendationsAdmin)
admin.site.register(UserRegistration, UserRegistrationAdmin)
admin.site.register(MealCategory)
