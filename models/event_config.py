#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@author: Link 
@contact: zheng.long@shoufuyou.com
@module: event_config
@date: 2018/7/9 
"""

import logging
from sqlalchemy import Column, String, Float
from models.base import Base

logger = logging.getLogger(__name__)


class EventConfig(Base):
    __tablename__ = 'EventConfig'

    event_key = Column(String(100), unique=True, comment='检查的关键字')
    comment = Column(String(100), comment='event_key 说明')

    threshold_low = Column(Float, comment='报警级别为 low 的阈值')
    threshold_mid = Column(Float, comment='报警级别为 medium 的阈值')
    threshold_high = Column(Float, comment='报警级别为 high 的阈值')
