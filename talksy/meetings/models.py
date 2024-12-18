import uuid
from datetime import datetime

from django.db import models
from django.utils import timezone

from talksy.settings import SERVER_LINK
from users.models import User
from utils import token


class Meeting(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=128, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField()  # YYYY-MM-DDTHH:MM:SSZ | 2024-12-18T15:30:00Z
    end_time = models.DateTimeField()
    token = models.CharField(max_length=100, null=False, blank=False)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = token.generate_token(50)
        super().save(*args, **kwargs)

    @property
    def status(self):
        """
        Dynamically calculates the current meeting status.
        """
        now = timezone.now()
        if now < self.start_time:
            return 'inactive'
        elif self.start_time <= now <= self.end_time:
            return 'active'
        return 'completed'

    @property
    def link(self):
        """
        Generates a link to a meeting.
        # -> https://talksy.ru/api/v1/meeting/<meeting_uuid>/<token>/join/
        """
        return f'{SERVER_LINK}/api/v1/meetings/{self.id}/{self.token}/join/'

    @property
    def update_token(self):
        try:
            self.token = token.generate_token(50)
        except Exception as e:
            return f'Unable to generate token: {e}'

        return self.token


class MeetingMembership(models.Model):
    ROLE_CHOICES = (
        ('host', 'Ведущий'),
        ('participant', 'Участник'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    anonymous_id = models.CharField(max_length=64, null=True, blank=True, unique=True)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    role = models.CharField(max_length=64, choices=ROLE_CHOICES, default='participant')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'meeting', 'anonymous_id')

    def __str__(self):
        return f"{self.user or self.anonymous_id} in {self.meeting}"
