import shutup
import logging
import warnings
from pprint import pprint

from time import sleep

from . import extractor, caller
from .connectors import telegram, webchat
from .database import resolver, broker
from .settings import LOG_DIR_PATH_AND_SEP, IS_DEBUG


def console_input():
    print('Write a sentence or write "exit"')
    while True:
        message = input().lower()
        if 'exit' == message:
            break

        parsed_message = extractor.parse(message)
        response = caller.run_action_from_parsed_message(parsed_message, '-1')
        print(response.get_printable_string())


def get_test_query(message: str):
    logging.info('Sending message: "%s"', message)

    parsed_message = extractor.parse(message)
    response = caller.run_action_from_parsed_message(parsed_message, '-1')
    print(response.get_printable_string())


if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    LOG_DIR_PATH_AND_SEP.mkdir(parents=True, exist_ok=True)

    log_path = LOG_DIR_PATH_AND_SEP / 'sherbot.log'
    # logging.basicConfig(filename=log_path, level=logging.INFO)
    logging.basicConfig(level=logging.INFO)

    logging.info('Starting the bot...')

    resolver.load_db_concept()
    broker.load_db_schema()
    broker.load_db_view()
    broker.test_connection()
    extractor.load_model()

    logging.info('Bot successfully started!')

    if not IS_DEBUG:
        webchat.start()
        # telegram.start()
        # console_input()
    else:
        logging.warning("Running in debug mode: executing predefined queries")
        get_test_query("find teachers")
        get_test_query("find teacher Matera")
        get_test_query('/cross_rel{"rel":"in research area"}')
