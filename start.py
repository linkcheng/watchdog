#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@author: Link
@contact: zheng.long@shoufuyou.com
@module: start
@date: 2018/7/9
@usage:
    python celery -A task.workers worker -c 2 --loglevel=info
    python start.py init
    python start.py run --name sample
    python start.py run --name monitor
    python start.py recall --start '2018-07-10 00:01:00' --end '2018-07-17 18:01:00'
"""
import logging
from concurrent.futures import ThreadPoolExecutor

import click
from influxdb import InfluxDBClient

from config.DB import INFLUXDB_CONFIG
from config.APP import (
    LOG_PATH,
    INFLUXDB_DATABASE_NAME
)
from util.log import configure_logging;configure_logging(LOG_PATH)
from util.tools import now_dt
from util.transfer import t2s, s2t
from util.misc import TimeSeries
from task.workers import async_sampler, async_monitor

logger = logging.getLogger('start')


def run_sampler():
    now = now_dt()
    logger.info(f'Start sampler time: [{t2s(now)}]')
    async_sampler(t2s(now.replace(second=0)))


def run_monitor():
    end = get_monitor_time_str()
    if end:
        logger.info(f'Start monitor time: [{end}]')
        async_monitor(end)


def recall(start: str, end: str=''):
    """历史数据回溯"""
    # --start = '2018-07-10 00:01:00'
    # --end = '2018-07-17 18:01:00'
    start_time = s2t(start).replace(second=0)
    end_time = s2t(end).replace(second=0) if end else now_dt().replace(second=0)
    ts = TimeSeries(start_time, end_time, minutes=1)
    _map = ThreadPoolExecutor().map

    def f(e):
        ct = e.astimezone()
        async_sampler(t2s(e), ct)

    list(_map(f, ts))


def init_db():
    # mysql 配置表初始化
    from models.base import Meta
    from models.event_config import EventConfig
    Meta.metadata.create_all()

    # influxdb 初始化
    database = INFLUXDB_DATABASE_NAME
    client = InfluxDBClient(**INFLUXDB_CONFIG, database=database)

    # 创建数据库 watchdog
    client.create_database(database)
    # 创建 Retention Policy:
    # 1. 采样数据保留策略，2w，默认保留策略
    client.create_retention_policy('rp_2_weeks', '2w', '1',
                                   database=database, default=True)
    # 2. 统计数据保留策略，5w
    client.create_retention_policy('rp_5_weeks', '5w', '1',
                                   database=database)
    # 3. 统计数据保留策略，26w
    client.create_retention_policy('rp_26_weeks', '26w', '1',
                                   database=database)
    # 创建 Continuous Query:
    # time 字段使用的是最小的时间
    # 比如：某一个分组 [2018-01-01T00:00:00Z, 2018-01-01T00:05:00Z)
    # 自动生成的 time = 2018-01-01T00:00:00Z
    cq1 = (f'CREATE CONTINUOUS QUERY cq_5_minutes ON {database} BEGIN '
           'SELECT sum(value) AS value, last(end_time) AS end_time '
           'INTO rp_5_weeks.eventLog FROM rp_2_weeks.sampledLog '
           'GROUP BY event_key, time(5m) '
           'END')

    client.query(cq1, method='POST')
    client.close()


def get_monitor_time_str():
    """计算监控时间"""
    database = INFLUXDB_DATABASE_NAME
    client = InfluxDBClient(**INFLUXDB_CONFIG, database=database)

    # 获取时间戳
    sql = 'SELECT time, last(end_time) AS end_time FROM rp_5_weeks.eventLog'
    ret = client.query(sql, epoch='s')
    points = list(ret.get_points())
    client.close()

    time_ts = points[0].get('end_time') if points else None
    time_str = t2s(s2t(time_ts)) if time_ts else ''

    return time_str


def influxdb_test():
    def timestamp_tz_ns(end: str):
        return int(s2t(end).astimezone().timestamp() * 1e9)

    end_str = '2018-07-18 18:00:00'
    end_time = timestamp_tz_ns(end_str)
    client = InfluxDBClient(**INFLUXDB_CONFIG, database=INFLUXDB_DATABASE_NAME)
    query_sql = ('SELECT value FROM rp_5_weeks.eventLog '
                 f"WHERE event_key='count_application2_success_5min' "
                 f"AND time<={end_time}")
    logger.info(query_sql)
    result = client.query(query_sql)
    for point in result.get_points():
        logger.info(point)
    client.close()


@click.command()
@click.argument('action', default='run', type=click.Choice(['run', 'init', 'recall']))
@click.option('--name', default='sample', type=click.Choice(['sample', 'monitor']))
@click.option('--start', '-start', default='')
@click.option('--end', '-end', default='')
def main(action, name, start, end):
    if action == 'run':
        fun = run_sampler if name == 'sample' else run_monitor
        fun()
    elif action == 'init':
        init_db()
    elif action == 'recall':
        recall(start, end)
    else:
        logger.info('Not existed action !')


if __name__ == '__main__':
    # influxdb_test()
    main()
