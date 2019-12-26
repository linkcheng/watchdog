#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@author: Link
@contact: zheng.long@sfy.com
@file: log.py
@time: 2018.04.10
"""
import os
import logging.config
from logging import ERROR, Logger

from util.error_track import track_error
from config.APP import ENABLE_TRACK

logger = logging.getLogger('logger')
default_log_path = './'

default_logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s %(filename)s line:%(lineno)d %(message)s'}
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },

    },

    'loggers': {
        'my_module': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': 'no'
        }
    },

    'root': {
        'level': 'INFO',
        'handlers': ['console', 'info_file_handler', 'error_file_handler']
    }
}

# time_info_file_handler = {
#     'class': 'logging.handlers.TimedRotatingFileHandler',
#     'level': 'INFO',
#     'formatter': 'simple',
#     'when': 'D',
#     'encoding': 'utf8',
# }
#
# time_error_file_handler = {
#     'class': 'logging.handlers.TimedRotatingFileHandler',
#     'level': 'ERROR',
#     'formatter': 'simple',
#     'when': 'D',
#     'encoding': 'utf8',
# }


size_info_file_handler = {
    'class': 'logging.handlers.RotatingFileHandler',
    'level': 'INFO',
    'formatter': 'simple',
    # 当达到 250MB 时分割日志
    'maxBytes': 262144000,
    # 最多保留 100 份文件
    'backupCount': 100,
    'encoding': 'utf8'
}

size_error_file_handler = {
    'class': 'logging.handlers.RotatingFileHandler',
    'level': 'ERROR',
    'formatter': 'simple',
    'maxBytes': 262144000,
    'backupCount': 50,
    'encoding': 'utf8'
}


def configure_logging(log_path=None):
    if not log_path:
        log_path = default_log_path
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    info_file_name = os.path.join(log_path, 'info.log')
    error_file_name = os.path.join(log_path, 'error.log')

    info_file_handler = size_info_file_handler
    error_file_handler = size_error_file_handler

    info_file_handler.update(filename=info_file_name)
    error_file_handler.update(filename=error_file_name)

    default_logging_config['handlers']['info_file_handler'] = info_file_handler
    default_logging_config['handlers']['error_file_handler'] = error_file_handler
    logging.config.dictConfig(default_logging_config)


def error(self, msg, *args, **kwargs):
    if self.isEnabledFor(ERROR):
        self._log(ERROR, msg, args, **kwargs)

    if ENABLE_TRACK:
        track_error(msg)


Logger.error = error


if __name__ == '__main__':
    configure_logging()
    logger = logging.getLogger('logger')
    logger.info('test logger')
