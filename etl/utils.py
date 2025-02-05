"""
Module: utils.py
Description: Provides general utility functions for date conversion, text encoding (base64),
and logging configuration (via the static method Utils.get_logger). Logs are maintained via a TimedRotatingFileHandler.
"""
import calendar
import time
import base64
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import os

class Utils:
    @staticmethod
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            log_file = os.path.join(os.path.dirname(__file__), "TRAI_etl_log.log")
            handler = TimedRotatingFileHandler(log_file, when="D", interval=1, backupCount=30)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    @staticmethod
    def convert_to_long_type(t, time_format):
        """
        Convert a datetime string to a long type (seconds since epoch).
        """
        try:
            dt = datetime.datetime.strptime(t, time_format)
            return int(dt.timestamp())
        except Exception as e:
            Utils.get_logger("utils").error("Error converting date {}: {}".format(t, e))
            raise

    @staticmethod
    def text_to_base64(text):
        """
        Encode the given text to a base64 string.
        """
        try:
            encoded_bytes = base64.b64encode(text.encode('utf-8'))
            return encoded_bytes.decode('utf-8')
        except Exception as e:
            Utils.get_logger("utils").error("Error encoding text to base64: {}".format(e))
            raise
