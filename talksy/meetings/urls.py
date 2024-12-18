from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import JoinMeetingView, MeetingListCreate, MeetingViewSet

router = DefaultRouter()
router.register(r'', MeetingViewSet, basename='meeting')

urlpatterns = [
    path('', MeetingListCreate.as_view(), name='list/createMeeting'),
    path('<uuid:meeting_id>/<token>/join/', JoinMeetingView.as_view(), name='join to the meeting'),

] + router.urls
