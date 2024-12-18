import secrets


def generate_token(length):
    """"
    Generates a token
    :param length: length of the token
    """
    return secrets.token_urlsafe(int((length + 1) / 2))[:length]
