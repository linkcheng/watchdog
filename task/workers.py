#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@author: Link 
@contact: zheng.long@shoufuyou.com
@module: workers
@date: 2018/7/9
"""
import logging
from datetime import timedelta
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

from influxdb import InfluxDBClient

from config.DB import INFLUXDB_CONFIG
from config.APP import (
    LOG_PATH, DB_URL, DB_NAME,
    ACTIVE_EVENT_KEYS,
    INFLUXDB_DATABASE_NAME,
    MIN_ALERT_VALUE
)
from util.log import configure_logging;configure_logging(LOG_PATH)
from util.error_track import track_error, track_warn, track_info
from util.transfer import s2t
from util.misc import get_lib_cls

from models import get_session
from models.event_config import EventConfig as Config
from task.app import app, Task

logger = logging.getLogger('workers')

executor = ThreadPoolExecutor()
map_ = executor.map


class Sampler:
    measurement = 'sampledLog'
    default_retention_policy = 'rp_2_weeks'

    def __init__(self, end: str, created_time=None, default=None):
        """
        采样 end-1m ~ end 时间之内的数据
        :param end: 采样结束时间
        :param created_time: 数据落库时间
        :param default: 默认值
        """
        self.classes = get_lib_cls()
        self.end = end
        self.created_time = created_time
        self.default = default

        self.closed = False
        self.client = InfluxDBClient(**INFLUXDB_CONFIG, database=INFLUXDB_DATABASE_NAME)
        self.session = get_session(DB_URL, DB_NAME, autocommit=True)
        self.q = Queue()
        self.qsize = 0

    def __del__(self):
        self.close()

    def sample(self, event_key):
        cls = self.classes.get(event_key)
        val = cls(self.end).sample_value() if cls else self.default
        self.q.put((event_key, {"value": val, "end_time": self.end}))

    def write_logs(self):
        json_body = []

        for _ in range(self.qsize):
            event_key, values = self.q.get(timeout=60)
            body = {
                "measurement": self.measurement,
                "tags": {
                    "event_key": event_key
                },
                "fields": values,
            }

            time_dt = self.created_time or s2t(self.end).astimezone()+timedelta(minutes=-1)
            time_dt.replace(second=0)
            body.update(time=time_dt)
            json_body.append(body)

        self.client.write_points(json_body, time_precision='s',
                                 retention_policy=self.default_retention_policy)
        self.client.close()

    def start(self):
        logging.info(f'Start end time at [{self.end}]')

        cs = self.session.query(Config.event_key).filter(Config.active == True)
        event_keys = [c.event_key for c in cs
                      if not ACTIVE_EVENT_KEYS or c.event_key in ACTIVE_EVENT_KEYS]
        self.qsize = len(event_keys)

        list(map_(lambda event_key: self.sample(event_key), event_keys))
        self.write_logs()

        return True

    def close(self):
        if not self.closed:
            if self.session:
                self.session.close()


class Monitor:
    measurement = 'monitoringLog'
    default_retention_policy = 'rp_26_weeks'

    def __init__(self, end: str):
        self.classes = get_lib_cls()
        self.end = end

        self.closed = False
        self.client = InfluxDBClient(**INFLUXDB_CONFIG, database=INFLUXDB_DATABASE_NAME)
        self.session = get_session(DB_URL, DB_NAME, autocommit=True)
        self.q = Queue()
        self.qsize = 0

    def __del__(self):
        self.close()

    def compute(self, event_key):
        cls = self.classes.get(event_key)
        if cls:
            obj = cls(self.end)
            real_value = obj.real_value()
            expected_values = obj.expect_values()
            start = obj.start
        else:
            logger.error(f'event_key:[{event_key}] can find monitor !')
            real_value, expected_values = None, {}
            start = None

        return {
            'start_time': start,
            'end_time': self.end,
            'real_value': real_value,
            **expected_values,
        }

    def run(self, event_key, threshold_high, threshold_mid, threshold_low,
            **kwargs):
        # 根据配置计算结果
        values = self.compute(event_key)

        # 根据计算结果分析
        real_value = values.get('real_value') or 0.0
        expected_value = values.get('expected_value') or 0.0
        mean_value = values.get('mean_value') or 0.0

        re_delta = expected_value - real_value
        rm_delta = mean_value - real_value

        # 有期望值并且 delta_abs 大于一定数值比如 4，才开启报警
        if (expected_value
                and re_delta > MIN_ALERT_VALUE
                and rm_delta > MIN_ALERT_VALUE):
            high_exp = round(expected_value * threshold_high, 2)
            mid_exp = round(expected_value * threshold_mid, 2)
            low_exp = round(expected_value * threshold_low, 2)

            high_m = round(mean_value * threshold_high, 2)
            mid_m = round(mean_value * threshold_mid, 2)
            low_m = round(mean_value * threshold_low, 2)

            msg = (f'Event key={event_key} \n'
                   f'Real value={real_value} \n'
                   f'Expected value={expected_value} \n'
                   f'Mean value={mean_value} \n'
                   f'Real-Expected={re_delta} \n'
                   f'Real-Mean={rm_delta} \n'
                   f'Threshold expected high={high_exp} \n'
                   f'Threshold expected mid={mid_exp} \n'
                   f'Threshold expected low={low_exp} \n'
                   f'Threshold mean high={high_m} \n'
                   f'Threshold mean mid={mid_m} \n'
                   f'Threshold mean low={low_m}.')

            if re_delta > high_exp and rm_delta > high_m:
                track_error(msg)
            elif re_delta > mid_exp and rm_delta > mid_m:
                track_warn(msg)
            elif re_delta > low_exp and rm_delta > low_m:
                logger.info(msg)

        # 计算结果写入日志
        self.q.put((event_key, values))

    def write_logs(self):
        json_body = []

        for _ in range(self.qsize):
            event_key, values = self.q.get()
            body = {
                "measurement": self.measurement,
                "tags": {
                    "event_key": event_key
                },
                "time": s2t(self.end).astimezone(),
                "fields": values,
            }
            json_body.append(body)

        self.client.write_points(json_body, time_precision='s',
                                 retention_policy=self.default_retention_policy)
        self.client.close()

    def start(self):
        logging.info(f'Start end time at [{self.end}]')

        cs = self.session.query(Config).filter(Config.active == True)
        configs = [c.to_dict() for c in cs]
        self.qsize = len(configs)

        list(map_(lambda config: self.run(**config), configs))
        self.write_logs()

        return True

    def close(self):
        if not self.closed:
            if self.session:
                self.session.close()


@app.task(base=Task, ignore_result=True)
def sampler(end):
    return Sampler(end).start()


@app.task(base=Task, ignore_result=True)
def monitor(end):
    return Monitor(end).start()


async_sampler = sampler.delay
async_monitor = monitor.delay
