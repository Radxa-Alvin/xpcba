#!/usr/bin/python3
from datetime import datetime

import sqlalchemy
from sqlalchemy import (Column, MetaData, String, Table, Text,
                        UniqueConstraint, create_engine)
from sqlalchemy.exc import IntegrityError

from utils import sqlite_db

engine = create_engine(sqlite_db('httpd.db'))
connect = engine.connect()
metadata = MetaData()


base = Table('base', metadata,
    Column('db', String(50), nullable=False),
    Column('name', String(50), nullable=False),
    Column('value', Text, nullable=False),
    UniqueConstraint('db', 'name', name='uix_1')
)

metadata.create_all(engine)
