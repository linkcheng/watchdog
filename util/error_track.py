#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@author: Link
@contact: zheng.long@sfy.com
@module: error_track
@date: 2018/7/6
"""
import sys

from util.tools import now_dt
from util.transfer import t2s
from config.APP import IGNORE_EXCEPTIONS

try:
    from config.APP import SENTRY_DSN
except ImportError:
    SENTRY_DSN = None


client = None
if SENTRY_DSN:
    from raven import Client
    client = Client(dsn=SENTRY_DSN)


def track(message=None, level='error', **kwargs):
    """
    跟踪接口，根据是否存在 sys.exc_info()判断 使用captureMessage 或 captureException
    :param message: error消息描述
    :param level: 同 sentry 一致，默认为 error 级别
    :param kwargs: dicts， 其它接口信息，支持 extra, tags, request 等等
    :return:
    """
    if not client:
        return

    exc_info = sys.exc_info()
    data = dict(tags={})

    # 如果存在异常信息，则调用 captureException 跟踪堆栈
    if exc_info[0]:
        exc_type = exc_info[1].__class__.__name__
        if exc_type in IGNORE_EXCEPTIONS:
            return

        data['tags']['type'] = exc_type
        client.captureException(exc_info=exc_info, level=level, data=data, **kwargs)
    else:
        # 如果 message 为空，则为 captureMessage 生成一个 message
        if not message:
            timestamp = t2s(now_dt())
            message = f'{client.name}, {timestamp}'
        client.captureMessage(message, level=level, data=data, **kwargs)


def track_debug(message=None, **kwargs):
    return track(message=message, level='debug', **kwargs)


def track_info(message=None, **kwargs):
    return track(message=message, level='info', **kwargs)


def track_warn(message=None, **kwargs):
    return track(message=message, level='warning', **kwargs)


def track_error(message=None, **kwargs):
    return track(message=message, **kwargs)

