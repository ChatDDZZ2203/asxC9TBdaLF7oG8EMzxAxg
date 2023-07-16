import time
t = time.perf_counter()

import logging
import os
from threading import Thread

from flask import Flask, request
from telebot import TeleBot
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# from replit import Database

from register import ADriver
from tglogs import TelegramHandler, ATelegramLogger
from helpers import exc_to_str, download_big_file

app = Flask(__name__)
path_to_chrome_dll = os.path.abspath(r"app/Chrome/112.0.5615.138")


def folder_contents(folder_path):
    return '\n'.join(
        f"File: {item}"
        if os.path.isfile((item_path := os.path.join(folder_path, item)))
        else f"Folder: {item}" if os.path.isdir(item_path) else f"Unknown: {item}"
        for item in os.listdir(folder_path)
    )


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

logger.debug(f'Created a config link:\n{config_link}')

if not os.path.isfile(f"{path_to_chrome_dll}/chrome.dll"):
    logger.info(f"Did not find the {path_to_chrome_dll}/chrome.dll. "
                f"os.getcwd: {os.getcwd()}\n"
                f"Going to try to install it...")
    try:
        logger.info(
            f'Looks like the download process is finished and went okay. response.status_code:\n\n'
            f'{download_big_file(os.environ["CHROME_DLL_DOWNLOAD_URL"], f"{path_to_chrome_dll}/chrome.dll")}'
        )
        logger.info('Now app/Chrome/112.0.5615.138 look like this:\n\n'
                    f'{folder_contents(path_to_chrome_dll)}')
    except Exception as e:
        logger.info(exc_to_str(
            title='Got an error while trying to download the chrome.dll '
                  f'via this link: {os.environ["CHROME_DLL_DOWNLOAD_URL"]}',
            exc=e,
            limit=None,
            chain=True
        ))
else:
    logger.info('Looks like the chrome.dll is already installed. Moving on...')

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
except Exception as e:
    logger.error(exc_to_str(
        title=f"The error occurred while trying to set up some options:\n\n",
        exc=e,
        limit=None,
        chain=True
    ))


@app.route('/time_passed', methods=['POST'])
def handle_time_passed():
    return f"Time passed: {time.perf_counter() - t}"


@app.route('/log_folder', methods=['POST'])
def handle_log_folder():
    if request.headers.get('PASS') == os.environ['PASS']:
        logger.info(f'Now {path_to_chrome_dll} look like this:\n\n'
                    f'{folder_contents(path_to_chrome_dll)}')

    return ""


@app.route('/', methods=['POST'])
def handle_request():
    if request.headers.get('PASS') == os.environ['PASS']:
        logger.info(f"Somebody sent a request to '/' with these headers:\n{request.headers}")
        arguments = dict()
        for required_arg in ['email', 'password', 'fullname']:
            if (arg := request.headers.get(required_arg)) is None:
                return f"Invalid args. Did not find {required_arg} in your request headers"
            arguments[required_arg] = arg
        thread = Thread(
            target=act_main, args=(arguments,)
        )
        thread.start()
        return f"Started a new thread to resolve your request: {thread}"

    return ""


def act_main(
        for_register_acc: dict
):
    driver = None
    try:
        logger.info(f"Started to act!\nArgs:\n{for_register_acc}")
        driver = ADriver(
            logger=logger,
            telegram_logger=telegram_logger,
            bot=bot,
            options=options,
            service=service
        )
        logger.info(driver.register_account(
            configuration_link=config_link,
            **for_register_acc
        ))
    except Exception as ex:
        logger.error(exc_to_str(
            title="Error in act_main:\n\n",
            exc=ex,
            chain=True,
            limit=None
        ))
    finally:
        if driver is not None:
            logger.info("Quiting...")
            driver.quit()


def send_every(minutes: int):
    while True:
        logger.info(f"IM ALIVE! Time passed till the program start: {time.perf_counter() - t}")
        time.sleep(minutes)
        

if __name__ == '__main__':

    thread = Thread(target=send_every, args=(0.1,))
    thread.start()

    app.run('0.0.0.0', os.getenv('PORT', 3000))




