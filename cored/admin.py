from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Resume, Job

admin.site.register(User, UserAdmin)
admin.site.register(Resume)
admin.site.register(Job)


