from django.urls import re_path

from .consumers import MeetingsConsumer

websocket_urlpatterns = [
    re_path(r'ws/api/v1/meetings/(?P<meeting_uuid>[a-f0-9\-]+)/$', MeetingsConsumer.as_asgi())
]
