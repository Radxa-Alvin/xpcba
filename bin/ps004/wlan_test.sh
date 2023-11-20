#!/bin/bash

set -e

nmcli dev wifi connect "ps004" password "12345678"

ETHER_WS_FILE=/tmp/wlan0_ws_file.txt
ETHER_RS_FILE=/tmp/wlan0_rs_file.txt
ret_wlan_ws=0
ret_wlan_rs=0
ret_wlan_ws_gb=0
ret_wlan_rs_gb=0
ret_wlan_ws_1=9
ret_wlan_ws_1=9

server_ip=192.168.31.58

WLAN0=`ifconfig -a  | grep mtu | awk '{print  $1}' | sed -n '5p' | sed 's/.$//'`

echo "wlan: $WLAN0"

WLAN_IP=`ifconfig -a  | grep netmask | awk '{print  $2}' | sed -n '3p'`

echo "wlan_ip:$WLAN_IP"

route add  -host $server_ip  metric 100 dev $WLAN0

iperf3 -c $server_ip -B $WLAN_IP -t 5   > $ETHER_WS_FILE
sleep 0.5
iperf3 -c $server_ip -B $WLAN_IP -R -t 5 -P 4 > $ETHER_RS_FILE 
sleep 0.5

ret_wlan_rs=`cat $ETHER_RS_FILE  | grep SUM | awk '{print $6}' | tail -n 1`

if [ $? == 0 ]; then
    echo "ret_wlan_rs is ok"
else
    echo "ret_wlan_rs  is err"
fi
echo "ret_wlan_rs : $ret_wlan_rs"

ret_wlan_rs_gb=`cat $ETHER_RS_FILE | grep SUM | awk '{print $7}' | tail -n 1`
if [ ${ret_wlan_rs_gb} == "Mbits/sec" ]; then
    echo "ret_wlan_rs_gb is ok"
else
    echo "ret_wlan_rs_gb  is err"
    echo "<wlan0_test>,<FAIL>,<-1>"
    exit 1
fi

ret_wlan_ws=`cat ${ETHER_WS_FILE} | grep "receiver" | awk '{print $7}'`
if [ $? == 0 ]; then
    echo "ret_wlan_ws is ok"
else
    echo "ret_wlan_ws  is err"
fi

echo "ret_wlan_ws : $ret_wlan_ws"

ret_wlan_ws_gb=`cat ${ETHER_WS_FILE} | grep "receiver" | awk '{print $8}'`
if [ ${ret_wlan_ws_gb} == "Mbits/sec" ]; then
    echo "ret_wlan_ws_gb is ok"
else
    echo "ret_wlan_ws_gb  is err"
    echo "<wlan0_test>,<FAIL>,<-1>"
    exit 1
fi

sleep 1

route del  -host $server_ip metric 100 dev $WLAN0
ret_wlan_ws_1=`awk  -v  num1="$ret_wlan_ws" -v num2=500  'BEGIN{print(num1>num2)?"0":"1"}'`
ret_wlan_rs_1=`awk  -v  num3="$ret_wlan_rs" -v num4=500  'BEGIN{print(num3>num4)?"0":"1"}'`

if [ $ret_wlan_ws_1 -eq 0 ]; then
    if [ $ret_wlan_rs_1  -eq 0 ]; then
        echo "<wlan0_test,ws:$ret_wlan_ws,rs:$ret_wlan_rs>,<PASS>,<0>"
        exit 0
    else
        echo "<wlan0_test,ws:$ret_wlan_ws,rs:$ret_wlan_rs>,<FAIL>,<-1>"
        exit 1
    fi
else
    echo "<wlan_test>,<FAIL>,<-2>"
    exit 2
fi

echo "<wlan_test>,<FAIL>,<-3>"
exit 3

