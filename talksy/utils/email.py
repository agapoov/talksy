from random import randint

from django.core.mail import send_mail


def generate_code():
    """"
    Генерирует 6 значный код
    """
    return randint(100000, 999999)


def sending_email(subject, message, from_email, user_email):
    """
    Универсальная функция для отправки почты.

    :param subject: Тема письма.
    :param message: Сообщение письма.
    :param from_email: Адрес отправителя.
    :param user_email: Адрес получателя.
    """
    send_mail(subject, message, from_email, [user_email])
