from rest_framework.authtoken.models import Token


def get_tokens_for_user(user):
    """
    Генерирует JWT-токены для пользователя.
    """
    token, created = Token.objects.get_or_create(user=user)

    return {
        'auth_token': str(token.key),
    }
