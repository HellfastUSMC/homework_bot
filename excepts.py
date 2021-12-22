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
    """Исключение при проверки что домашки не являются списком."""

    pass
