from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.username} - {self.first_name} {self.last_name}'
