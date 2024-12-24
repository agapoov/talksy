from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_confirmed = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.username} - {self.first_name} {self.last_name}'


class BlockHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField(null=True, blank=True)
    blocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blocked_users')
    blocked_at = models.DateTimeField(auto_now_add=True)
