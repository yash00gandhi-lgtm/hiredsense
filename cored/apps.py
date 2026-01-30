from django.apps import AppConfig
from django.contrib.auth import get_user_model
import os

class CoredConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cored"

    def ready(self):
        User = get_user_model()

        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if username and password:
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
