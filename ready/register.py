import base64
import time
import logging
import functools

from telebot import TeleBot
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as ec
from selenium.common import exceptions

from tglogs import ATelegramLogger
from helpers import exc_to_str, random_sleep

class ADriver(Chrome):
    def __init__(
            self,
            logger: logging.getLogger,
            telegram_logger,
            bot: TeleBot,
            wait_options: dict = None,
            options=None,
            service=None,
            keep_alive: bool = True
    ):
        super().__init__(
            options=options,
            service=service,
            keep_alive=keep_alive
        )
        self.logger = logger
        self.bot = bot
        self.telegram_logger = telegram_logger
        self.wait = WebDriverWait(
            driver=self, **wait_options
        ) if wait_options is not None else WebDriverWait(driver=self, timeout=15)

    def put_in_cycle(
            self,
            possible_exceptions: tuple,
            min_secs_sleep: float = 1,
            max_secs_sleep: float = 2,
            times_to_try: int = 10
    ):
        def wrapper(func):
            @functools.wraps(func)
            def new_func(*args, **kwargs):
                for i in range(times_to_try):
                    try:
                        return func(*args, **kwargs)
                    except possible_exceptions as e:
                        self.logger.error(exc_to_str(
                            e, f"EXCEPTION ON {i + 1} iteration of {func.__name__} cycle:\n\n", None
                        ))
                        random_sleep(min_secs_sleep, max_secs_sleep)
            return new_func
        return wrapper

    def save_screenshot_tg(
            self,
            selector: tuple
    ):
        try:
            self.telegram_logger.send_photo(
                ATelegramLogger.DEBUG,
                base64.b64decode(self.find_element(*selector).screenshot_as_base64)
            )
        except Exception as e:
            self.logger.error(f"ERROR IN save_screenshot: {exc_to_str(e)}")
    
    def tab(
            self,
            max_n: int = 10
    ):
        actions = ActionChains(self)
        for i in range(max_n):
            actions.send_keys(Keys.TAB).perform()
            actions.reset_actions()
            random_sleep(max([0.01, 0.23 - i / 100]), max([0.02, 0.5 - i / 100]))
    
    def register_account(self, email: str, password: str, full_name: str, configuration_link: str):
        time.sleep(1)
        self.get(configuration_link)
        time.sleep(2)

        self.get("https://apilayer.com/signup")
        self.wait.until(ec.presence_of_element_located(
            (By.XPATH, '//*[@id="signinSrEmail"]')
        ))

        self.put_in_cycle(
            possible_exceptions=(exceptions.ElementNotInteractableException,)
        )(
            self.find_element(By.XPATH, '//*[@id="signinSrEmail"]').send_keys
        )(email)

        random_sleep(2, 4)
        self.put_in_cycle(
            possible_exceptions=(exceptions.ElementNotInteractableException,)
        )(
            self.find_element(By.XPATH, '//*[@id="signinSrPassword"]').send_keys
        )(password)

        random_sleep(0.5, 2)
        self.find_element(By.XPATH, '//*[@id="signinSrConfirmPassword"]').send_keys(password)

        random_sleep(1.5, 3)
        self.find_element(By.XPATH, '//*[@id="signinSrName"]').send_keys(full_name)

        random_sleep(1, 3.5)
        Select(self.find_element(By.CSS_SELECTOR, 'select#country')).select_by_value('US')
        random_sleep(0.4, 1)

        self.put_in_cycle(
            possible_exceptions=(exceptions.ElementNotInteractableException,),
            min_secs_sleep=2, max_secs_sleep=3, times_to_try=35
        )(
            self.find_element(By.XPATH, '//*[@id="signinSrName"]').click
        )()

        r = self.find_element(By.XPATH, '//*[@id="signinSrName"]')
        random_sleep(1, 2)
        r.click()

        self.tab(7)
        ActionChains(self).send_keys(Keys.SPACE).perform()

        self.tab(5)
        ActionChains(self).send_keys(Keys.SPACE).perform()

        try:
            self.wait.until(
                ec.presence_of_element_located(
                    (By.CSS_SELECTOR, f'''a[href="/verify-account-again?email={email.replace('@', '%40')}"]''')
                )
            ).click()
            return f"Finished registering with these credentials::\n\nemail: {email}\n" \
                   f"password: {password}\nfull_name: {full_name}"

        except Exception as e:
            return exc_to_str(
                e,
                title="Was not able to find an element that shows that everything went fine "
                      "(The resend email element). Got an exception:\n\n",
                limit=None,
                chain=True
            )
            
            
            