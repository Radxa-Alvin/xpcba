#!/usr/bin/python3
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.client import Client

host = '192.168.31.245'
port = 6688
debug = True
board = 'rs102'

client = Client(host, port, debug)
client.enter(board)

item0 = {
    'cmd': 'init_env',
    'type': 'external',
    'file': 'bin/rs102/init_env.py',
    'hook': {
        'load': 'push:bin/rs102/utils.py:/tmp/xpcba/utils.py'
    }
}

item1 = {
    'cmd': 'cpu_test',
    'type': 'external',
    'file': 'bin/rs102/cpu_test.py'
}

item2 = {
    'cmd': 'ddr_test',
    'type': 'external',
    'file': 'bin/rs102/ddr_test.py',
    'args': 2040
}

item3 = {
    'cmd': 'sd_test',
    'type': 'external',
    'file': 'bin/rs102/sd_test.py'
}

item4 = {
    'cmd': 'emmc_test',
    'type': 'external',
    'file': 'bin/rs102/emmc_test.py',
    'args': 14.6
}

item5 = {
    'cmd': 'bt_test',
    'type': 'external',
    'file': 'bin/rs102/bt_test.py'
}

item6 = {
    'cmd': 'wlan_test',
    'type': 'external',
    'file': 'bin/rs102/wlan_test.py'
}

item7 = {
    'cmd': 'usb_test_cc1',
    'type': 'external',
    'file': 'bin/rs102/usb_test.py',
    'args': 'cc1'
}

item8 = {
    'cmd': 'usb_test_cc2',
    'type': 'external',
    'file': 'bin/rs102/usb_test.py',
    'args': 'cc2'
}

item9 = {
    'cmd': 'i2c_time_test',
    'type': 'external',
    'file': 'bin/common/i2c_time_test.sh',
    'args': [ 'radxa,zero', 5, 3 ]
}

item10 = {
    'cmd': 'i2c_time_test',
    'type': 'external',
    'file': 'bin/common/i2c_time_test.sh',
    'args': [ 'radxa,zero2', 0, 3 ]
}

client.test(item0)
client.test(item1)
client.test(item2)
client.test(item3)
client.test(item4)
client.test(item5)
client.test(item6)
client.test(item7)
client.test(item8)
client.test(item9)
client.test(item10)
