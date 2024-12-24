from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'', views.UserActionViewSet, basename='UserAction')

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('verify/', views.UserVerifyEmailView.as_view(), name='emil-verify'),
    path('login/', views.UserLoginView.as_view(), name='login'),

] + router.urls
