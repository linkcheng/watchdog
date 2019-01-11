#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@author: Link
@contact: zheng.long@shoufuyou.com
@module: tools
@date: 2018/5/22
"""
import time
import logging
import cProfile
import pytz
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)
str_tz_fmt = '%Y-%m-%dT%H:%M:%SZ'
str_fmt = '%Y-%m-%d %H:%M:%S'
str_fmt_date = '%Y-%m-%d'
time_start = datetime(1970, 1, 1)

now_int = time.time
now_dt = datetime.now
now_utc_dt = datetime.utcnow
now = now_int
now_tzinfo = now_dt().astimezone().tzinfo
utc_tzinfo = pytz.timezone('UTC')


def fn_timer(fn):
    """
    计算 fn 的运算时间
    :param fn:
    :return:
    """
    @wraps(fn)
    def function_timer(*args, **kwargs):
        start = now()
        result = fn(*args, **kwargs)
        logger.info(f'{fn.__name__} total running time {now() - start} seconds')
        return result

    return function_timer


@contextmanager
def timer(name='default'):
    """
    计算代码段的运行时间
    :param name: 用于区分不同代码段的名称
    :return:
    :usage:  with timer('delay'):
                 time.sleep(3)
    """
    start = now()
    yield
    logger.info(f'{name} total running time {now() - start} seconds')


def profiler(fn):
    """
    print_stats(sort)
    sort 排序参数
    -1: "stdname",
    0:  "calls",
    1:  "time",
    2:  "cumulative"

    :param fn:
    :return:
    gprof2dot -f pstats run.cprof | dot -Tpng -o run.png

    """
    @wraps(fn)
    def _profiler(*args, **kwargs):
        profile = cProfile.Profile()
        result = profile.runcall(fn, *args, **kwargs)
        profile.dump_stats(f'profile/{fn.__name__}.cprof')
        # profile.print_stats(2)
        return result

    return _profiler


def fake_exception():
    try:
        1 / 0
    except ZeroDivisionError as e:
        logger.error(e)
