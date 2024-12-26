import uuid

from cryptography.fernet import Fernet
from django.conf import settings
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

    def __str__(self):
        return f'Собрание {self.title}. Создатель {self.creator}'

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
        # -> https://talksy.ru/api/v1/meetings/<meeting_uuid>/<token>/join/
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
    CONNECTION_STATUS = (
        ('no data', 'Нет данных'),
        ('pending', 'Подтверждено, но не активно'),
        ('active', 'Активно'),
        ('closed', 'Закрыто'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    anonymous_id = models.CharField(max_length=64, null=True, blank=True, unique=True)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    role = models.CharField(max_length=64, choices=ROLE_CHOICES, default='participant')
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=128, choices=CONNECTION_STATUS, default='no data')

    class Meta:
        unique_together = ('user', 'meeting', 'anonymous_id')

    def __str__(self):
        return f"{self.user or self.anonymous_id} in {self.meeting}"


class MeetingMessage(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    sender_id = models.CharField(max_length=1024)
    encrypted_message = models.TextField(max_length=1024, null=False, blank=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message by {self.sender_id} in {self.meeting}'

    @property
    def content(self):
        """"
        decryption before sending
        """
        cipher_suite = Fernet(settings.ENCRYPTION_KEY)
        return cipher_suite.decrypt(self.encrypted_message.encode()).decode()

    @content.setter
    def content(self, message_content):
        """"
        encryption before sending
        """
        if not isinstance(message_content, str):
            raise ValueError("Message content must be a string.")
        cipher_suite = Fernet(settings.ENCRYPTION_KEY)
        self.encrypted_message = cipher_suite.encrypt(message_content.encode()).decode()
