#!/usr/bin/env python
# encoding: utf-8

"""
@version: v1.0
@author: Gaivin Wang
@license: Apache Licence
@contact: gaivin@outlook.com
@site: https://github.com/gaivin/
@software: PyCharm
@file: logger_utils.py
@time: 6/8/2018 3:43 PM
"""

__author__ = 'WangGang'

import os
import logging

# Logger configuration
LOGGER_LEVEL_DEFAULT = "DEBUG"
LOGGER_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = ".\logs"


def get_logger(logger_name, log_dir=LOG_DIR, level=LOGGER_LEVEL_DEFAULT, logger_format=LOGGER_FORMAT):
    logger = logging.getLogger(logger_name)
    logger.propagate = 0
    if os.path.exists(log_dir):
        pass
    else:
        os.makedirs(log_dir)
    file_handler = logging.FileHandler(os.path.join(log_dir, "%s.log" % logger_name), 'a', encoding='utf-8')
    # file_handler = logging.FileHandler(os.path.join(log_path, "%s.log" % logger_name))
    stream_handler = logging.StreamHandler()
    if hasattr(logging, level):
        logger_level = getattr(logging, level)
    else:
        logger_level = logging.DEBUG
    logger.setLevel(logger_level)
    detail_formatter = logging.Formatter(logger_format)
    file_handler.formatter = detail_formatter
    stream_handler.formatter = detail_formatter
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
