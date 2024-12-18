from django.contrib import admin

from .models import Meeting, MeetingMembership

admin.site.register(Meeting)
admin.site.register(MeetingMembership)
