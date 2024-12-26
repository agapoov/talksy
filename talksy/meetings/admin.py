from django.contrib import admin

from .models import Meeting, MeetingMembership, MeetingMessage

admin.site.register(Meeting)
admin.site.register(MeetingMembership)
admin.site.register(MeetingMessage)
