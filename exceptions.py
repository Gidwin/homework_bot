class NotStatusOkException(Exception):
    """Исключение статуса ответа."""

    pass


class NoDeliveryMessage(Exception):
    """Недоставленно сообщение в телеграмм."""
    pass
