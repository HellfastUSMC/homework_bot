class TokenMissing(Exception):
    """Исключение для отсутствующих токенов."""

    pass


class ResponseWrongStatus(Exception):
    """Исключение для кода запроса не равного 200."""

    pass


class ResponseUnknownError(Exception):
    """Исключение для других ошибок запроса."""

    pass


class ResponseEmptyHW(Exception):
    """Исключение для пустого списка домашних работ."""

    pass


class ResponseNotAListHW(Exception):
    """Исключение при проверкe что домашки не являются списком."""

    pass


class ResponseNotAJSON(Exception):
    """Исключение при проверкe что домашки не являются списком."""

    pass


class ResponseNotADict(Exception):
    """Исключение при проверкe что домашки не являются списком."""

    pass


class ResponseMissingKeys(Exception):
    """Исключение при проверкe что домашки не являются списком."""

    pass


class StatusUnknown(Exception):
    """Исключение при проверкe статуса в словаре."""

    pass


class MessageNotSent(Exception):
    """Исключение при неотправке сообщения."""

    pass
