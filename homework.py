import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (NoDeliveryMessage, NotStatusOkException)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info('Сообщение отправлено')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        logging.info('Отправляю запрос к API ЯндексПрактикума')
        answer_endpoint = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if answer_endpoint.status_code != HTTPStatus.OK:
            raise NotStatusOkException('Недоступность эндпоинта')
        return answer_endpoint.json()
    except ConnectionError:
        raise ConnectionError('Сбой при запросе к эндпоинту')


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('API передал не словарь')
    homework = response.get('homeworks')
    if homework is None:
        raise KeyError('API не содержит ключа homeworks')
    if not isinstance(homework, list):
        raise TypeError('Содержимое не список')
    return homework


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('В ответе API нет ключа homework_name')
    homework_status = homework.get('status')
    if homework_status is None:
        raise KeyError('В ответе API нет ключа homework_status')
    if homework_status not in VERDICTS:
        raise KeyError('Неизвестный статус домашней работы')
    verdict = VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens_bool = True
    if PRACTICUM_TOKEN is None:
        tokens_bool = False
    if TELEGRAM_TOKEN is None:
        tokens_bool = False
    if TELEGRAM_CHAT_ID is None:
        tokens_bool = False
    return tokens_bool


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        filename='error.log',
        filemode='a',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    if check_tokens():
        logging.info('Токены впорядке')
    else:
        logging.critical(
            'Не обнаружен один из ключей PRACTICUM_TOKEN,'
            'TELEGRAM_TOKEN, TELEGRAM_CHAT_ID'
        )
        raise sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                if homework:
                    logger.info(
                        'Сообщение об изменении статуса работы отправлено.'
                    )
                    send_message(bot, parse_status(homework))
            logger.info('Статус работы не изменился.')
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except NoDeliveryMessage as error:
            logger.error(f'Сообщение в Telegram не отправлено: {error}')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.critical(message)
            time.sleep(RETRY_TIME)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.addHandler(
        logging.StreamHandler()
    )
    main()
