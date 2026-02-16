from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from core.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    search_fields = ("username", "email", "first_name", "last_name")

# Register your models here.

# Register any remaining models from the core app that do not have a custom admin.
for model in apps.get_app_config("core").get_models():
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass
