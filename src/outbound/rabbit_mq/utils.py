RETRY_ATTEMPT_HEADER = "x-retry-attempt"


def get_retry_attempt(headers: dict) -> int:
    """Номер текущей попытки обработки, 0 если это первая попытка.

    :param headers: заголовки сообщения RabbitMQ.
    :return: номер попытки из заголовка x-retry-attempt.
    """
    return int(headers.get(RETRY_ATTEMPT_HEADER, 0))
