#!/usr/bin/python3
from utils import cache_get, output

host = cache_get('host')

if not host:
    print('<ping_test>,<FAIL>,<-2>')
    exit(1)

cmd = f'ping -c 10 -I wlan0 {host}'

if '0% packet loss' in output(cmd):
    print('<ping_test>,<PASS>,<0>')
else:
    print('<ping_test>,<FAIL>,<-1>')
