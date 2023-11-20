#!/usr/bin/python3
import os
import sys

CURDIR = os.path.dirname(os.path.abspath(__file__))


def apply():
    for root, _, files in os.walk(os.path.join(CURDIR, 'vendor')):
        for f in [f for f in files if f.endswith('.whl')]:
            sys.path.insert(0, os.path.join(root, f))
