#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@author: Link 
@contact: zheng.long@sfy.com
@module: __init__.py 
@date: 2018/7/9 
"""
import logging
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base


logger = logging.getLogger(__name__)


@lru_cache(maxsize=64)
def get_db(url, name, pool_size=20, pool_recycle=3600):
    logger.info(f'Connecting {name} ...')
    conn = create_engine(url, pool_size=pool_size, pool_recycle=pool_recycle,
                         pool_pre_ping=True, encoding='utf-8')
    logger.info(f'{name} connected')
    # 建立数据路连接
    return conn


@lru_cache(maxsize=64)
def get_base(url, name):
    logger.info(f'Getting {name} base ...')
    # 建立数据路连接
    db = get_db(url, name)
    Base = automap_base(declarative_base(db), name=name)
    Base.prepare(db, reflect=True)
    logger.info(f'{name} base got')
    return Base


def get_session(url, name, autocommit=False):
    # 建立数据路连接
    bind = get_db(url, name)
    session_factory = sessionmaker(bind=bind, autocommit=autocommit)
    session = scoped_session(session_factory)
    sess = session()
    return sess