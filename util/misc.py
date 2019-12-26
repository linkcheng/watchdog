#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@author: Link
@contact: zheng.long@sfy.com
@module: misc
@date: 2018/7/9
"""
import os
import sys
import json
import logging
from array import array
from functools import partial
from datetime import datetime, timedelta, date
from collections import Iterable, Mapping

import numpy as np
from werkzeug.utils import find_modules, import_string

int_array = partial(array, 'i')
uint_array = partial(array, 'I')
float_array = partial(np.array, dtype=float)

logger = logging.getLogger(__name__)


def get_lib_cls():
    """
    从 lib 包下，加载包含 event_key 属性的类
    :return:
    """
    _current_path = os.path.abspath(os.path.dirname(__file__))
    _father_path = os.path.abspath(os.path.dirname(_current_path) + os.path.sep + '.')
    if _father_path not in sys.path:
        sys.path.append(_father_path)

    return {field_type._event_key: field_type
            for name in find_modules('lib')
            for field, field_type in import_string(name).__dict__.items()
            if hasattr(field_type, '_event_key')}


class TimeSeries(object):
    def __init__(self, start_time: datetime, end_time: datetime,
                 days=0, hours=0, minutes=0):
        if days == hours == minutes == 0:
            raise RuntimeError('days, hours, minutes can not be set all zero !')
        self.current = start_time
        self.end_time = end_time
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.__is_stop = False

    def __iter__(self):
        return self

    def next(self):
        if self.__is_stop:
            raise StopIteration

        current = self.current

        self.current += timedelta(days=self.days, hours=self.hours, minutes=self.minutes)
        if self.current >= self.end_time:
            self.__is_stop = True

        return current

    __next__ = next


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)


def freehash(arg):
    try:
        return hash(arg)
    except Exception:
        if isinstance(arg, Mapping):
            return hash(frozendict(arg))
        elif isinstance(arg, Iterable):
            return hash(frozenset(freehash(item) for item in arg))
        else:
            return id(arg)


class frozendict(dict):
    """ An implementation of an immutable dictionary. """
    def __delitem__(self, key):
        raise NotImplementedError("'__delitem__' not supported on frozendict")

    def __setitem__(self, key, val):
        raise NotImplementedError("'__setitem__' not supported on frozendict")

    def clear(self):
        raise NotImplementedError("'clear' not supported on frozendict")

    def pop(self, key, default=None):
        raise NotImplementedError("'pop' not supported on frozendict")

    def popitem(self):
        raise NotImplementedError("'popitem' not supported on frozendict")

    def setdefault(self, key, default=None):
        raise NotImplementedError("'setdefault' not supported on frozendict")

    def update(self, *args, **kwargs):
        raise NotImplementedError("'update' not supported on frozendict")

    def __hash__(self):
        return hash(frozenset((key, freehash(val)) for key, val in self.items()))


if __name__ == '__main__':
    print(get_lib_cls())
