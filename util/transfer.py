#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import logging
from datetime import datetime
from util.tools import str_fmt

logger = logging.getLogger(__name__)

ts2t = datetime.fromtimestamp


def s2d(val, fmt=str_fmt):
    """字符串转date"""
    if val is None:
        return None
    val = ensure_unicode(val)
    ret = s2t(val, fmt)

    return ret.date() if ret else None


def s2t(val, fmt=str_fmt):
    """字符串转datetime"""
    if val is None:
        return None
    val = ensure_unicode(val)
    val, *end = val.split(".")
    try:
        ret = datetime.strptime(val, fmt) if val else None
    except Exception as e:
        logger.error(str(e))
        ret = None
    return ret


def t2s(d, fmt='%Y-%m-%d %H:%M:%S'):
    """
     datetime  转 字符串
    :param d:  datetime
    :param fmt:  str 日期字符串
    :return:
    """
    return d.strftime(fmt)


def s2i(val, default=None):
    """字符串转整数"""
    if val is None:
        return default

    val = ensure_unicode(val)

    return int(val) if val.isdigit() or val[1:].isdigit() else default


def s2f(val, default=None):
    """字符串转小数"""
    if val is None:
        return default

    val = ensure_unicode(val)

    if val.isdigit() or val[1:].isdigit():
        ret = float(val)
    elif '.' in val:
        try:
            ret = float(val)
        except Exception as e:
            logger.error(str(e))
            ret = default
    else:
        ret = default
    return ret


def s2num(val, default=None):
    """低效将字符串转数字，但兼容性好"""
    if val is None:
        return default

    val = ensure_unicode(val)

    if val.isdigit() or val[1:].isdigit():
        ret = int(val)
    elif '.' in val:
        try:
            ret = float(val)
        except Exception as e:
            logger.error(str(e))
            ret = default
    else:
        ret = default
    return ret


def b2s(val):
    """byte -> str"""
    if isinstance(val, bytes):
        val = val.decode('utf-8')
    else:
        val = str(val)

    return val


def s2b(val):
    """str -> byte"""
    if val is None:
        return None

    if isinstance(val, str):
        val = val.encode('utf-8')
    else:
        val = bytes(val)

    return val


def ensure_unicode(val):
    return b2s(val)


if __name__ == '__main__':
    from util.log import configure_logging
    configure_logging()
    now = datetime.now()
    print(t2s(now))
    print(s2num('是'))
    print(s2num('否'))
    print(s2num(''))
    print(s2num('1'))
    print(s2num('1.0'))
    print(s2num('-1'))
    print(s2num('-1.0'))
    print(s2f(''))
    print(s2f(1))
    print(s2f(1.0))
    print(s2f('1'))
    print(s2f('-1'))
    print(s2f('1.2'))
    print(s2f('-1.2'))
    print(s2f('1.a'))
    print(s2i(1))
    print(s2i(''))
    print(s2i('2'))
    print(s2i('2.0'))
    print(s2i('-2'))
    print(s2t('2018-01-01 10:00:00', '%Y-%m-%d %H:%M:%S'))
    print(s2d('2018-01-01 10:00:00', '%Y-%m-%d %H:%M:%S'))
