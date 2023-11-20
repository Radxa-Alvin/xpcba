#!/usr/bin/python3
import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def get_path(fname, basedir=BASEDIR, not_exist_mk=True):
    if not os.path.isabs(fname):
        fname = os.path.join(basedir, fname)
    if not_exist_mk:
        parent = os.path.dirname(fname)
        if not os.path.exists(parent):
            os.makedirs(parent) 
    return os.path.abspath(fname)


def sqlite_db(name):
    return f'sqlite:///{get_path(name)}?check_same_thread=False'
