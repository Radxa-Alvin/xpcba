#!/usr/bin/python3
import sys
import subprocess

DDR_SIZE = int(sys.argv[-1])

shell = lambda x: subprocess.check_call(x, shell=True)
output = lambda x: subprocess.check_output(x, shell=True).decode()


def main():
    x = output("cat /proc/zoneinfo | grep present | awk 'BEGIN{a=0}{a+=$2}END{print a}'")
    size = int(x.strip()) * 4 / 1024
    if 0.95 < (size / DDR_SIZE) < 1.05:
        print(f'<ddr_test, {int(size)}MB>,<PASS>,<0>')
    else:
        print(f'<ddr_test, {int(size)}MB>,<FAIL>,<-1>')


if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        print(ex)
        print('<ddr_test, app_error>,<FAIL>,<-2>')
