from django.contrib import admin

from .models import BlockHistory, User

admin.site.register(User)
admin.site.register(BlockHistory)
