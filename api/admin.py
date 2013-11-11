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
    list_display = ('username', 'phone_number', 'last_name', 'first_name', 'email', 'is_active')

    def phone_number(self, user):
        return user.profile.phone_number

class RestaurantAdmin(admin.ModelAdmin):
    # FIXME: symbolic names for 'location'
    list_display = ('name', 'location')
    search_fields = ['name']
    list_filter = ['location']

class MealAdmin(admin.ModelAdmin):
    # FIXME: show pic_url somehow (thumbnail?)
    list_display = ('restaurant', 'name', 'price')

    search_fields = ['name', 'restaurant__name']
    list_filter = ['restaurant__name']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ('time', 'email', 'restaurant', 'pos_slip_number', 'status')

    def email(self, order):
        return order.user.email

    search_fields = ['user__email', 'restaurant__name']
    list_filter = ['restaurant']
    date_hierarchy = 'time'

class MealRecommendationsAdmin(admin.ModelAdmin):
    list_display = ('email', 'restaurant_name', 'meal_name')

    def email(self, recommendation):
        return recommendation.user.email

    def restaurant_name(self, recommendation):
        return recommendation.meal.restaurant.name

    def meal_name(self, recommendation):
        return recommendation.meal.name

    search_fields = ['user__email', 'meal__name']
    list_filter = ['user']

class UserRegistrationAdmin(admin.ModelAdmin):
    inlines = [ProfileInline]
    list_display = ('user', 'uuid', 'clicked')

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), MyUserAdmin)
admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Meal, MealAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(MealRecommendation, MealRecommendationsAdmin)
admin.site.register(UserRegistration, UserRegistrationAdmin)
