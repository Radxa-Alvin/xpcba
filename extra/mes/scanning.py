#!/usr/bin/python3
import xml.etree.ElementTree as el

from utils import cache_get, cache_set, http_get, output

KEY = 'uUQFKhdAacN9c2av'


def get_subnet(ifdev):
    res = output(f"ip route | egrep -m 1 /.*{ifdev} | awk '{{print $1}}'")
    return res.strip()


def find_elem(child, key, var):
    return list(filter(lambda x: x.get(key) == var, child))


def nmap_addr(subnet, port):
    res = output(f'nmap -oX - -n -p {port} -T5 {subnet}')

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


def ping_addr(host):
    try:
        resp = http_get(f'http://{host}:8083/ping', timeout=3)
        if resp.read() == b'pong':
            return True
    except Exception as ex:
        print(ex)
    return False


def find_addr(ifdev, port, key):
    addr = cache_get(key)
    if addr:
        if ping_addr(addr):
            return addr
        else:
            cache_set(key, None, _del=True)

    subnet = get_subnet(ifdev)
    for addr in nmap_addr(subnet, port):
        if ping_addr(addr):
            cache_set(key, addr)
    return addr


def get_scan(ifdev, port=8083, key='scan'):
    addr = find_addr(ifdev, port, key)
    cpuid = output("cat /proc/cpuinfo | grep Serial | awk '{print $3}'").strip()
    resp = http_get(f'http://{addr}:8083/pong', {'key': KEY, 'cpuid': cpuid}, timeout=3)
    text = resp.read().decode()
    if text in ['hello', 'empty']:
        return 'empty'
    return text


if __name__ == '__main__':
    text = get_scan('eth0')
    print(text)
