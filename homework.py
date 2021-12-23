import logging
import requests
import telegram
import telegram.ext
import time
import logging.config

from dotenv import load_dotenv
from http import HTTPStatus
from os import getenv, path

from exceptions import (ResponseEmptyHW, TokenMissing,
                        ResponseWrongStatus, ResponseUnknownError,
                        StatusUnknown, MessageNotSent, ResponseNotAJSON,
                        ResponseMissingKeys)

load_dotenv()
logging.config.fileConfig(
    path.join(path.dirname(__file__), 'logging.ini'),
    disable_existing_loggers=False
)

PRACTICUM_TOKEN = getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения ботом."""
    logger = logging.getLogger('send_message')
    msg = bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

    if msg['text'] != message:
        status = 'не отправлено'
        logger.error(status)
        raise MessageNotSent(status)

    else:
        logger.info('отправлено')


def get_api_answer(current_timestamp):
    """Получение ответа от API домашки."""
    logger = logging.getLogger('get_api_answer')
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    reason = HTTPStatus(response.status_code).phrase

    if reason == HTTPStatus.NOT_FOUND.phrase:
        message = f'Код ответа { reason }, ресурс не найден'
        logger.error(message)
        raise ResponseWrongStatus(message)

    elif reason != HTTPStatus.OK.phrase:
        message = f'Код ответа { reason } != {HTTPStatus.OK.phrase}'
        logger.error(message)
        raise ResponseWrongStatus(message)

    else:
        logger.info('Ответ от API получен')
        try:
            resp_dict = response.json()
        except Exception as exc:
            message = f'При преобразовании из JSON возникла проблема { exc }'
            logger.error(message)
            raise ResponseNotAJSON(message)
        else:
            return resp_dict


def check_response(response):
    """Проверка полученного в get_api_answer() запроса."""
    logger = logging.getLogger('check_response')
    if not isinstance(response, dict):
        message = 'Запрос не является словарем!'
        logger.error(message)
        raise TypeError(message)

    elif not isinstance(response['homeworks'], list):
        message = 'Домашние работы не являются списком!'
        logger.error(message)
        raise TypeError(message)

    elif not response['homeworks']:
        message = 'Список работ пуст!'
        logger.error(message)
        raise ResponseEmptyHW(message)

    elif response['homeworks']:
        homeworks = response['homeworks']
        logger.info('Запрос проверен')
        return homeworks

    else:
        message = 'Неизвестная ошибка запроса!'
        logger.error(message)
        raise ResponseUnknownError(message)


def parse_status(homework):
    """Сопоставление статуса из словаря и формирование сообщения в чат."""
    logger = logging.getLogger('parse_status')

    if not homework['homework_name'] or not homework['status']:
        message = 'В запросе отсутствуют ключи homework_name или status'
        logger.error(message)
        raise ResponseMissingKeys(message)

    else:
        homework_name = homework['homework_name']
        homework_status = homework['status']

        if homework_status not in HOMEWORK_STATUSES:
            message = 'Статус с таким обозначением не найден в словаре'
            logger.error(message)
            raise StatusUnknown(message)

        else:
            verdict = HOMEWORK_STATUSES[homework_status]
            logger.info('Сформирован текст сообщения')
            return ('Изменился статус проверки работы'
                    f' "{homework_name}". {verdict}')


def check_tokens():
    """Проверка токенов в окружении."""
    logger = logging.getLogger('check_tokens')
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        logger.info('Токены на месте')
        return True

    else:
        return False


def main():
    """Основная логика работы бота."""
    logger = logging.getLogger(__name__)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_hw = None
    logger.info('Бот запущен...')

    while True:

        try:

            if not check_tokens():
                message = 'Один из токенов отсутствует!'
                logger.critical(message)
                raise TokenMissing(message)

            else:
                api_answer = get_api_answer(current_timestamp)
                last_homework = check_response(api_answer)[0]
                message = parse_status(last_homework)

                if prev_hw == last_homework['status']:
                    logger.debug('Статус домашки не изменился')

                elif prev_hw is None:
                    prev_hw = last_homework['status']
                    logger.info('Сообщение с'
                                ' первоначальным статусом')
                    send_message(bot, message)

                else:
                    prev_hw = last_homework['status']
                    logger.info('Сообщение с'
                                ' обновленным статусом')
                    send_message(bot, message)
                    current_timestamp = int(time.time())

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.info(message)
            time.sleep(RETRY_TIME)

        else:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
