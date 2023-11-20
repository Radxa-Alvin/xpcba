#!/usr/bin/python3
import argparse
import time

from utils import cache_get, cache_set, http_get, http_post, output

try:
    import xml.etree.ElementTree as el
except Exception as ex:
    print(ex)

KEY = 'uUQFKhdAacN9c2av'


def get_subnet(ifdev):
    x = output(f"ip route | egrep -m 1 /.*{ifdev} | awk '{{print $1}}'")
    return x.strip()


def find_elem(child, key, var):
    return list(filter(lambda x: x.get(key) == var, child))


def find_addr(args):
    res = output(f'nmap -oX - -n -p 8082 -T5 {args.subnet}')
    if args.debug:
        print(res)

    addr = []
    for host in el.fromstring(res.encode()).iter('host'):
        for x in host:
            if x.tag == 'status':
                if find_elem(host, 'state', 'up') and find_elem(host, 'reason', 'arp-response'):
                    tmp = find_elem(host, 'addrtype', 'ipv4')
                    addr.append(tmp[0].get('addr'))
            if x.tag == 'ports':
                if find_elem(x[0], 'state', 'open') and find_elem(x[0], 'reason', 'syn-ack'):
                    tmp = find_elem(host, 'addrtype', 'ipv4')
                    addr.append(tmp[0].get('addr'))
    return addr


def check_http(host):
    try:
        resp = http_get(f'http://{host}:8082/ping', timeout=2)
        if resp.read() == b'pong':
            return True
    except Exception as ex:
        print(ex)
    return False


def check_free(host):
    try:
        resp = http_post(f'http://{host}:8082/free', dict(key=KEY))
        if resp.read() == b'free':
            return True
    except Exception as ex:
        print(ex)
    return False


def find_http(args):
    if not args.subnet:
        for x in args.ifdev.split(' '):
            args.subnet = get_subnet(x)
            if args.subnet:
                break
        else:
            print('<get_host>,<FAIL>,<-3>')
            return

    http = []
    for addr in find_addr(args):
        if check_http(addr):
            http.append(addr)
        cache_set('http', http)
    return http


def find_free(args):
    http = cache_get('http') or find_http(args)
    if not http:
        print('<get_host>,<FAIL>,<-2>')
        return

    for _ in range(args.timeout):
        for addr in http:
            if check_free(addr):
                cache_set('host', addr)
                print(f'<get_host, {addr}>,<PASS>,<0>')
                return
        time.sleep(1)
    else:
        cache_set('http', _del=True)
        print('<get_host, timeout>,<FAIL>,<-3>')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host')
    parser.add_argument('-i', '--ifdev')
    parser.add_argument('-s', '--subnet')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-t', '--timeout', default=30, type=int)
    args = parser.parse_args()

    try:
        if args.host:
            cache_set('http', [args.host])
        find_free(args)
    except Exception as ex:
        print(ex)
        print('<get_host>,<FAIL>,<-1>')
