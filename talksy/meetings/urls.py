from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MeetingListCreate, MeetingViewSet

router = DefaultRouter()
router.register(r'', MeetingViewSet, basename='meeting')

urlpatterns = [
    path('', MeetingListCreate.as_view(), name='list/createMeeting'),

] + router.urls
