from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from master.models import Currency


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    search_fields = ("name", "code", "symbol")

# Register your models here.

# Register any remaining models from the master app that do not have a custom admin.
for model in apps.get_app_config("master").get_models():
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass
