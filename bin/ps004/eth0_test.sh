#!/bin/bash

ETHER_WS_FILE=/tmp/ether0_ws_file.txt
ETHER_RS_FILE=/tmp/ether0_rs_file.txt
ret_ether_ws=0
ret_ether_rs=0
ret_ether_ws_gb=0
ret_ether_rs_gb=0
ret_ether_ws_1=9
ret_ether_ws_1=9
server_ip=192.168.31.58

ETH0=`ifconfig -a  | grep mtu | awk '{print  $1}' | sed -n '1p' | sed 's/.$//'`

echo "eth0: $ETH0"

ETH0_IP=`ifconfig -a  | grep netmask | awk '{print  $2}' | sed -n '1p'`

echo "eth0_ip:$ETH0_IP"

route add  -host $server_ip  metric 100 dev $ETH0

iperf3 -c $server_ip -B $ETH0_IP -t 5   > $ETHER_WS_FILE
sleep 0.5
iperf3 -c $server_ip -B $ETH0_IP -R -t 5 -P 4 > $ETHER_RS_FILE 
sleep 0.5

ret_ether_rs=`cat $ETHER_RS_FILE  | grep SUM | awk '{print $6}' | tail -n 1`

if [ $? == 0 ]; then
    echo "ret_ether_rs is ok"
else
    echo "ret_ether_rs  is err"
fi
echo "ret_ether_rs : $ret_ether_rs"

ret_ether_rs_gb=`cat $ETHER_RS_FILE | grep SUM | awk '{print $7}' | tail -n 1`
if [ ${ret_ether_rs_gb} == "Mbits/sec" ]; then
    echo "ret_ether_rs_gb is ok"
else
    echo "ret_ether_rs_gb  is err"
    echo "<eth0_test>,<FAIL>,<-1>"
    exit 1
fi

ret_ether_ws=`cat ${ETHER_WS_FILE} | grep "receiver" | awk '{print $7}'`
if [ $? == 0 ]; then
    echo "ret_ether_ws is ok"
else
    echo "ret_ether_ws  is err"
fi

echo "ret_ether_ws : $ret_ether_ws"

ret_ether_ws_gb=`cat ${ETHER_WS_FILE} | grep "receiver" | awk '{print $8}'`
if [ ${ret_ether_ws_gb} == "Mbits/sec" ]; then
    echo "ret_ether_ws_gb is ok"
else
    echo "ret_ether_ws_gb  is err"
    echo "<eth0_test>,<FAIL>,<-1>"
    exit 1
fi

sleep 1

route del  -host $server_ip metric 100 dev $ETH0
ret_ether_ws_1=`awk  -v  num1="$ret_ether_ws" -v num2=920  'BEGIN{print(num1>num2)?"0":"1"}'`
ret_ether_rs_1=`awk  -v  num3="$ret_ether_rs" -v num4=920  'BEGIN{print(num3>num4)?"0":"1"}'`

if [ $ret_ether_ws_1 -eq 0 ]; then
    if [ $ret_ether_rs_1  -eq 0 ]; then
        echo "<ether0_test,ws:$ret_ether_ws,rs:$ret_ether_rs>,<PASS>,<0>"
        exit 0
    else
        echo "<ether0_test,ws:$ret_ether_ws,rs:$ret_ether_rs>,<FAIL>,<-1>"
        exit 1
    fi
else
    echo "<ether_test>,<FAIL>,<-2>"
    exit 2
fi

echo "<ether_test>,<FAIL>,<-3>"
exit 3

