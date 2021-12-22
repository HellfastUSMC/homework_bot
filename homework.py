import logging
import requests
import telegram
import telegram.ext
import time

from dotenv import load_dotenv
from os import getenv

from excepts import (ResponseEmptyHW, ResponseNotAListHW, TokenMissing,
                     ResponseWrongStatus, ResponseUnknownError,
                     StatusUnknown, MessageNotSent)

load_dotenv()

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s -- [%(levelname)s] -- %(message)s'
)


def send_message(bot, message):
    """Отправка сообщения ботом."""
    msg = bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    if msg['text'] != message:
        status = 'Сообщение не отправлено'
        logging.error(status)
        raise MessageNotSent(status)
    else:
        logging.info('Сообщение отправлено')


def get_api_answer(current_timestamp):
    """Получение ответа от API домашки."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if response.status_code != 200:
        code = response.status_code
        message = f'Код ответа { code } != 200'
        logging.error(message)
        raise ResponseWrongStatus(message)

    else:
        logging.info('Ответ от API получен')
        return response.json()


def check_response(response):
    """Проверка полученного в get_api_answer() запроса."""
    if type(response['homeworks']) != list:
        message = 'Домашние работы не являются списком!'
        logging.error(message)
        raise ResponseNotAListHW(message)

    elif response['homeworks'] == []:
        message = 'Список работ пуст!'
        logging.error(message)
        raise ResponseEmptyHW(message)

    elif response['homeworks'] != []:
        homeworks = response['homeworks']
        logging.info('Запрос проверен')
        return homeworks

    else:
        message = 'Неизвестная ошибка запроса!'
        logging.error(message)
        raise ResponseUnknownError(message)


def parse_status(homework):
    """Сопоставление статуса из словаря и формирование сообщения в чат."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES.keys():
        message = 'Статус с таким обозначением не найден в словаре'
        logging.error(message)
        raise StatusUnknown(message)
    else:
        verdict = HOMEWORK_STATUSES[homework_status]
        logging.info('Сформирован текст сообщения')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов в окружении."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        logging.info('Токены на месте')
        return True

    else:
        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_hw = None
    logging.info('Бот запущен...')

    while True:

        try:

            if check_tokens() is False:
                message = 'Один из токенов отсутствует!'
                logging.critical(message)
                raise TokenMissing(message)

            else:
                api_answer = get_api_answer(current_timestamp)
                last_homework = check_response(api_answer)[0]
                message = parse_status(last_homework)

                if prev_hw == last_homework['status']:
                    logging.debug('Статус домашки не изменился')

                elif prev_hw is None:
                    prev_hw = last_homework['status']
                    send_message(bot, message)
                    logging.info('Отправлено сообщение с'
                                 ' первоначальным статусом')

                else:
                    send_message(bot, message)
                    prev_hw = last_homework['status']
                    current_timestamp = int(time.time())

                time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.info('Отправлено сообщение об ошибке')
            time.sleep(RETRY_TIME)

        else:
            message = 'Что-то пошло не так...'
            logging.info('Отправлено сообщение об ошибке')
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
