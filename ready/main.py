import logging
import os

from flask import Flask, request
from telebot import TeleBot
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# from replit import Database

from register import ADriver
from tglogs import TelegramHandler, ATelegramLogger
from helpers import exc_to_str

app = Flask(__name__)

@app.route('/', methods=['POST'])
def handle_request():
    if request.headers.get('PASS') == os.environ['PASS']:
        arguments = dict()
        for required_arg in ['email', 'password', 'full_name']:
            if (arg := request.headers.get(required_arg)) is None:
                return f"Invalid args. Did not find {required_arg} in your request headers"
            arguments[required_arg] = arg
        return act_main(arguments)

    return ""


def act_main(
        for_register_acc: dict
):
    try:
        driver = ADriver(
            logger=logger,
            telegram_logger=telegram_logger,
            bot=bot,
            options=options,
            service=service
        )
        driver.register_account(
            configuration_link=config_link,
            **for_register_acc
        )
    except Exception as ex:
        logger.error(exc_to_str(
            title="Error in act_main:\n\n",
            exc=ex,
            chain=True,
            limit=None
        ))


if __name__ == '__main__':

    bot = TeleBot(os.environ['TG_BOT_TOKEN'])
    # db = Database(os.environ['REPLIT_DB_URL'])
    config_link = os.environ['CONFIG_LINK'] % os.environ['ACONFIG']

    bot.parse_mode = 'html'

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s :\n%(message)s", '%Y-%m-%d %H:%M:%S')
    telegram_handler = TelegramHandler(bot, os.environ['TG_LOGS_CHAT_ID'], options={
        'reply_to_message_id': os.environ['TG_TOPIC_ID']
    })
    telegram_handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    logger.addHandler(telegram_handler)

    logger.debug(f"Created a config link:\n{config_link}")

    try:
        telegram_logger = ATelegramLogger(bot, os.environ['TG_LOGS_CHAT_ID'], ATelegramLogger.DEBUG, options={
            'send_photo_options': {'reply_to_message_id': os.environ['TG_TOPIC_ID']}
        })

        service = Service(executable_path=r'app/drivers/chromedriver_112.0.5615.49.exe')

        options = Options()
        for option in os.environ['options_list'].split(' '):
            options.add_argument(option)
        options.add_extension(r'app/extensions/noCaptchaAi-chrome-v1.1.crx')
        options.binary_location = r'app/Chrome/chrome.exe'

        logger.info('Running server...')
        app.run('0.0.0.0', os.getenv('PORT', 3000))
    except Exception as e:
        logger.error(exc_to_str(
            title=f"The error occurred while trying to set up some options and run a server:\n\n",
            exc=e,
            limit=None,
            chain=True
        ))


