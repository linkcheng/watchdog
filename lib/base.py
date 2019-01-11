#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@author: Link 
@contact: zheng.long@shoufuyou.com
@module: base 
@date: 7/23/18 
"""
import logging

import numpy as np
from scipy import stats
from abc import ABCMeta, abstractmethod
from influxdb import InfluxDBClient

from config.DB import INFLUXDB_CONFIG
from config.APP import (
    TABLE_CONFIG,
    MEAN_PERIOD,
    EXPECT_PERIOD,
    INFLUXDB_DATABASE_NAME
)
from models import get_base
from util.transfer import s2t
from util.misc import frozendict, uint_array, float_array

logger = logging.getLogger(__name__)


class Meta(ABCMeta):
    """
    通过 '_event_key', 'schema', 'table' 类属性，自动添加
    conf，model 属性。
    conf: 数据库表的配置信息，包括 url, created_time 与 updated_time 字段名称
    model: 数据库表对应的 ORM 模型
    """
    properties = {
        '_event_key', 'schema', 'table'
    }

    def __new__(mcs, name, bases, attrs):
        not_implemented_list = [p for p in mcs.properties if p not in attrs]
        is_abstarct = attrs.get('__abstract__', False)

        if not is_abstarct and not_implemented_list:
            raise NotImplementedError(f'{not_implemented_list} must be implemented !')

        if not is_abstarct:
            name = '.'.join([attrs['schema'], attrs['table']])
            conf = frozendict(TABLE_CONFIG.get(name))

            base = get_base(conf['url'], attrs['schema'])
            model = getattr(base.classes, attrs['table'])

            attrs.update(conf=conf, model=model)
        return super().__new__(mcs, name, bases, attrs)


class Base(metaclass=Meta):
    """基本，子类必须实现：event_key，timestamp 属性以及 sample_value 方法，如
    @property
    def event_key(self):
        return self._event_key

    @property
    def timestamp(self):
        return self.timestamp_ns(self.start)

    def sample_value(self):
        return 0

    real_value：采用的实际统计值
    expect_values：基于历史统计值预测当前时间的值

    """
    __abstract__ = True

    client = InfluxDBClient(**INFLUXDB_CONFIG,
                            database=INFLUXDB_DATABASE_NAME)
    least_mean_period = 3

    @property
    @abstractmethod
    def event_key(self):
        pass

    @property
    @abstractmethod
    def timestamp(self):
        """返回 rp_5_weeks.eventLog 中使用的时间戳"""
        pass

    @abstractmethod
    def sample_value(self):
        pass

    @staticmethod
    def timestamp_ns(end: str):
        return int(s2t(end).timestamp() * 1e9)

    def real_value(self):
        """统计值"""
        query_sql = ("SELECT value FROM rp_5_weeks.eventLog "
                     f"WHERE event_key='{self.event_key}' "
                     f"AND time={self.timestamp}+1m")
        ret = self.client.query(query_sql)
        self.client.close()
        points = list(ret.get_points())

        return points[0].get('value') if points else None

    def expect_values(self):
        mv = self.mean_value()
        lv = self.linear_value()
        return {'mean_value': mv, 'expected_value': lv}

    def linear_value(self):
        """线性回归值"""
        sql = ("SELECT value FROM rp_5_weeks.eventLog "
               f"WHERE event_key='{self.event_key}' "
               f"AND time<{self.timestamp} "
               f"AND time>={self.timestamp}-{EXPECT_PERIOD}m")
        ret = self.client.query(sql)
        self.client.close()

        value = None
        y = float_array([point.get('value') for point in ret.get_points()])
        if y.size > 5:
            next_x = len(y)
            x = float_array(range(next_x))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            value = round(intercept + slope * next_x)

        return value if value is None or value > 0 else 0.0

    def mean_value(self):
        """算数平均值"""

        if MEAN_PERIOD < 2:
            return None

        def build_sql(key):
            return ("SELECT value FROM rp_5_weeks.eventLog "
                    f"WHERE event_key='{self.event_key}' "
                    f"AND time={self.timestamp}+1m-{key}d")

        sqls = ';'.join([build_sql(i+1) for i in range(MEAN_PERIOD + self.least_mean_period)])
        rets = self.client.query(sqls)
        self.client.close()

        value = None
        values = uint_array(sorted((point.get('value') for ret in rets
                                   for point in ret.get_points())))
        length = len(values)
        if length >= MEAN_PERIOD or length >= self.least_mean_period:
            pivot = (length + 1) // 2 if length % 2 else length // 2
            median = values[pivot]
            high = int(median * 2.5)
            low = int(median * 0.4)

            valida_values = uint_array(v for v in values if low < v < high)
            value = int(np.mean(valida_values)) if valida_values else None

        return value


if __name__ == '__main__':
    pass
