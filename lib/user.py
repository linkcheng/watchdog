#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@author: Link 
@contact: zheng.long@shoufuyou.com
@module: application2
@date: 2018/7/23
"""
import logging
from datetime import timedelta

from models import get_session
from lib.base import Base
from util.transfer import s2t, t2s

logger = logging.getLogger(__name__)


class User(Base):
    _event_key = 'count_user_5min'
    schema = 'shoufuyou_v2'
    table = 'User'

    def __init__(self, end: str):
        end_time = s2t(end).replace(second=0).astimezone()
        self.start_sample = t2s(end_time+timedelta(minutes=-1))
        self.start = t2s(end_time+timedelta(minutes=-5))
        self.end = t2s(end_time)

    @property
    def event_key(self):
        return self._event_key

    @property
    def timestamp(self):
        return self.timestamp_ns(self.start)

    def sample_value(self):
        url = self.conf.get('url')
        session = get_session(url, self.schema, autocommit=True)
        created_time = getattr(self.model, self.conf.get('created_time'))

        value = session.query(self.model). \
            filter(created_time >= self.start_sample,
                   created_time < self.end).count()

        session.close()
        return value


if __name__ == '__main__':
    m5 = User('2018-07-20 12:50:00')
    print(m5.event_key)
    print(m5.timestamp)
    # print(m5.sample_value())
    # print(m5.real_value())
    print(m5.expect_values())
