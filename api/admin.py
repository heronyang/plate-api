from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from api.models import *

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profiles'

class MyUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    list_display = ('email',  'phone_number', 'last_name', 'first_name')

    def phone_number(self, user):
        return user.profile.phone_number

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ('time', 'email', 'restaurant', 'pos_slip_number', 'status')

    def email(self, order):
        return order.user.email

    search_fields = ['user__email', 'restaurant__name']
    list_filter = ['time']
    date_hierarchy = 'time'

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), MyUserAdmin)
admin.site.register(Restaruant)
admin.site.register(Meal)
admin.site.register(Order, OrderAdmin)
admin.site.register(MealRecommendation)
