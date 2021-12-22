
import requests
import telegram
import telegram.ext
import time
from excepts import EmptyHW

from dotenv import load_dotenv
from os import getenv

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

'''def test():
    print(requests.get(ENDPOINT, headers=HEADERS, params={'from_date': int(time.time()) - 2629743}).json())

test()'''


def send_message(bot, message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    period = 0 #2629743
    timestamp = current_timestamp - period or int(time.time()) - period
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params).json()
    return response


def check_response(response):
    if response['homeworks'] != []:
        homeworks = response['homeworks']
        return homeworks
    else:
        raise EmptyHW('Список работ пуст!!!')


def parse_status(homework):
    homework_name = homework['lesson_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            api_answer = get_api_answer(current_timestamp)
            print('ApiANSW', api_answer)
            response = check_response(api_answer)[0]
            print('check_response', response)
            message = parse_status(response)
            print('message', message)
            send_message(bot, message)

            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print('msg', message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            message = 'щто??!'
            send_message(bot, message)


if __name__ == '__main__':
    main()
