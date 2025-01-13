from django.contrib import admin
from .models import PasswordReset, Task, Profile

# Register your models here.
admin.site.register(PasswordReset)
admin.site.register(Task)
admin.site.register(Profile)