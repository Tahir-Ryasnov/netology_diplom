import csv
import datetime

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from backend.models import User, Contact, OrderGood, Order


def export_to_csv(admin_, request, queryset):
    option = admin_.model._meta
    filename = f'{option.verbose_name}.scv'
    file = open(filename, 'w')
    writer = csv.writer(file)
    fields = [field for field in option.get_fields() if not field.many_to_many and not field.one_to_many]
    writer.writerow([field.verbose_name for field in fields])
    for object_ in queryset:
        data = list()
        for field in fields:
            value = getattr(object_, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime('%d/%m/%Y')
            data.append(value)
        writer.writerow(data)


class UserCreation(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ('email', )


class UserChange(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', )


class AdminUser(UserAdmin):
    add_form = UserCreation
    form = UserChange
    model = User
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('email', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'type')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'company', 'position')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}),
    )
    search_fields = ('email', )
    ordering = ('email', )


class AdminContact(admin.ModelAdmin):
    list_display = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'user', 'phone')
    list_display_links = ('user', )
    list_filter = ('user', 'city')


class GoodInLine(admin.TabularInline):
    model = OrderGood
    raw_id_fields = ['order', ]


@admin.register(Order)
class AdminOrder(admin.ModelAdmin):
    list_display = ['id', 'user', 'date', 'state', 'contact']
    list_filter = ['user', 'date']
    inlines = [GoodInLine]
    actions = [export_to_csv]


export_to_csv.short_description = 'Export to csv'
admin.site.register(User, AdminUser)
admin.site.register(Contact, AdminContact)
