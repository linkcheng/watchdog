#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@author: Link 
@contact: zheng.long@shoufuyou.com
@module: base
@date: 2018/7/9
"""
import logging
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

from config.APP import DB_URL, DB_NAME
from models import get_db, get_session

logger = logging.getLogger(__name__)


Meta = declarative_base(bind=get_db(DB_URL, DB_NAME), name=DB_NAME)


class Base(Meta):
    __abstract__ = True
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_time = Column(DateTime, default=datetime.now)
    updated_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    active = Column(Boolean, default=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in
                self.__table__.columns}

    @classmethod
    def insert(cls, value):
        session = get_session(DB_URL, DB_NAME)
        try:
            session.add(cls(**value))
        except Exception as exc:
            logger.error(exc)
            session.rollback()
        else:
            session.commit()
        finally:
            session.close()


if __name__ == '__main__':

    class TestModel(Base):
        __tablename__ = 'TestLog'

        id_card_number = Column(String(length=20))
        mobile = Column(String(length=20))
        name = Column(String(length=32))


    # Meta.metadata.create_all()
    sess = get_session(DB_URL, DB_NAME)
    result = sess.query(TestModel).filter(TestModel.name == 'xyf0').first()
    print(result.to_dict())
    sess.close()

