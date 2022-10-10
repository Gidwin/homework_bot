class NotStatusOkException(Exception):
    """Исключение статуса ответа."""

    pass


class NotTokenException(Exception):
    """Исключение нет необходимых токенов."""

    pass


class NoDelivaryMessage(Exception):
    """Недоставленно сообщение в телеграмм."""
    pass
