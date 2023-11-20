#!/usr/bin/python3
# pylint: disable=no-value-for-parameter
import json

from flask import Flask, request
from sqlalchemy.sql import and_, delete, insert, select, update

from model import IntegrityError, base, connect

app = Flask(__name__)
KEY = 'uUQFKhdAacN9c2av'
NOT_NAME = 'name cannot be empty'


@app.route('/', methods=['GET', 'POST'])
def index():
    return 'hello, django'


@app.route('/set', methods=['GET', 'POST'])
def _set():
    if request.values.get('key') != KEY:
        return 'hello, django'

    db = request.values.get('db', 'default')
    name = request.values.get('name')
    value = request.values.get('value')
    args = dict(db=db, name=name, value=value)

    if not name:
        return json.dumps({'msg': 'error', 'ex': NOT_NAME})

    try:
        stmt = insert(base).values(**args)
        connect.execute(stmt)
        resp = json.dumps({'msg': 'ok', 'op': 'insert'})
    except IntegrityError as ex:
        stmt = update(base).where(
            and_(base.c.db == db, base.c.name == name)
        ).values(value=value)
        connect.execute(stmt)
        resp = json.dumps({'msg': 'ok', 'op': 'update'})
    except Exception as ex:
        resp = json.dumps({'msg': 'error', 'ex': str(ex)})

    return resp


@app.route('/del', methods=['GET', 'POST'])
def _del():
    if request.values.get('key') != KEY:
        return 'hello, django'

    db = request.values.get('db', 'default')
    name = request.values.get('name')

    if not name:
        return json.dumps({'msg': 'error', 'ex': NOT_NAME})

    try:
        stmt = delete(base).where(
            and_(base.c.db == db, base.c.name == name))
        connect.execute(stmt)
        resp = json.dumps({'msg': 'ok', 'op': 'delete'})
    except Exception as ex:
        resp = json.dumps({'msg': 'error', 'ex': str(ex)})

    return resp


@app.route('/inc', methods=['GET', 'POST'])
def inc():
    if request.values.get('key') != KEY:
        return 'hello, django'

    db = request.values.get('db', 'default')
    name = request.values.get('name')
    value = request.values.get('value')
    args = dict(db=db, name=name, value=value)

    if not name:
        return json.dumps({'msg': 'error', 'ex': NOT_NAME})

    try:
        stmt = select([base]).where(
            and_(base.c.db == db, base.c.name == name))
        x = connect.execute(stmt).first()
        if x:
            value = str(int(value) + int(x[-1]))
            stmt = update(base).where(
                and_(base.c.db == db, base.c.name == name)
            ).values(value=value)
        else:
            stmt = insert(base).values(**args)
        connect.execute(stmt)
        resp = json.dumps({'msg': 'ok', 'value': value})
    except Exception as ex:
        resp = json.dumps({'msg': 'error', 'ex': str(ex)})

    return resp


@app.route('/get', methods=['GET', 'POST'])
def get():
    if request.values.get('key') != KEY:
        return 'hello, django'

    db = request.values.get('db', 'default')
    name = request.values.get('name')
    value = request.values.get('value')

    if not name:
        return json.dumps({'msg': 'error', 'ex': NOT_NAME})

    try:
        stmt = select([base]).where(
            and_(base.c.db == db, base.c.name == name))
        x = connect.execute(stmt).first()
        resp = json.dumps({'msg': 'ok', 'value': (x or [value])[-1]})
    except Exception as ex:
        resp = json.dumps({'msg': 'error', 'ex': str(ex)})

    return resp


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8094)
