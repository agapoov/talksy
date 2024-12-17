from celery import shared_task

from talksy import settings
from utils import email


@shared_task(bind=True, max_retries=3)
def send_2fa_email(self, user_email, code):
    try:
        subject = 'Talksy. Ваш 2FA код'
        message = f'Ваш код: {code}'
        from_email = settings.EMAIL_HOST_USER
        email.sending_email(subject, message, from_email, [user_email])
    except Exception as e:
        self.retry(exc=e, countdown=5)
