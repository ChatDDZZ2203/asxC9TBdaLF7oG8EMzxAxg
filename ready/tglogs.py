import logging
from collections import defaultdict

class TelegramHandler(logging.Handler):
    def __init__(self, bot, chat_id, options: dict = None):
        super().__init__()
        self.chat_id = chat_id
        self.bot = bot
        if options is None:
            options = {}
        self.options = options

    def emit(self, record):
        self.bot.send_message(
            chat_id=self.chat_id,
            text=self.format(record),
            **self.options
        )

class ATelegramLogger:
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    CRITICAL = 4

    def __init__(self, bot, chat_id, log_level: int = None, options: dict[str, dict] = None):
        """:param: log_level defaults to WARN (2)"""
        self.bot = bot
        self.chat_id = chat_id
        self.log_level = log_level if log_level is not None else self.WARN
        if options is None:
            options = {}
        self.options = defaultdict(dict, **options)

    def log_document(self, log_level: int, document_filename: str):
        if log_level >= self.log_level:
            with open(document_filename, "rb") as f:
                self.send_document(log_level, f)


    def send_document(self, log_level: int, file):
        if log_level >= self.log_level:
            self.bot.send_document(
                chat_id=self.chat_id,
                document=file,
                **self.options['send_document_options']
            )

    def log_photo(self, log_level: int, filename: str):
        if log_level >= self.log_level:
            with open(filename, "rb") as f:
                self.send_photo(log_level, f)

    def send_photo(self, log_level: int, file):
        if log_level >= self.log_level:
            self.bot.send_photo(
                chat_id=self.chat_id,
                photo=file,
                **self.options['send_photo_options']
            )
