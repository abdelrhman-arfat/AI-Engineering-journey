import logging
import sys


class Logger:

    _configured = False

    @staticmethod
    def _configure():
        if Logger._configured:
            return

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

        Logger._configured = True

    @staticmethod
    def info(message: str, name: str = "APP"):
        Logger._configure()
        logging.getLogger(name).info(message)

    @staticmethod
    def warning(message: str, name: str = "APP"):
        Logger._configure()
        logging.getLogger(name).warning(message)

    @staticmethod
    def error(message: str, name: str = "APP"):
        Logger._configure()
        logging.getLogger(name).error(message)

    @staticmethod
    def debug(message: str, name: str = "APP"):
        Logger._configure()
        logging.getLogger(name).debug(message)
