from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('verify/', views.UserVerifyEmailView.as_view(), name='emil-verify'),
    path('login/', views.UserLoginView.as_view(), name='login'),

]
