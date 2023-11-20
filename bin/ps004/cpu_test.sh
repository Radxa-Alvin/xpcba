#!/bin/bash

echo "I: Start testing CPU"

count=0
ret=0
CPUINFO=/tmp/cpuinfo.txt
cat /proc/cpuinfo | grep processor > $CPUINFO 
CPU_NUM=`cat $CPUINFO | awk 'END {print}' | awk '{print $3}'`
echo "CPUNUM:$CPU_NUM"
TOTAL=`expr $CPU_NUM + 1`
N=3

for nr in $(seq 0 $CPU_NUM)
do
   echo "nr:$nr"
   if [ "`cat /sys/bus/cpu/devices/cpu${nr}/online`" = "1" ]; then
       let count++
   fi
done

if [ "$count" = "$TOTAL" ]; then  
    for i in $(seq 0 6)
    do
        FREQUENCY_ALL=`cat /sys/bus/cpu/devices/cpu1/cpufreq/scaling_available_frequencies` 
        I=`expr $i + 1`	
        echo "FREQUENCY_ALL IS  $FREQUENCY_ALL"
        FREQUENCY[$I]=`echo ${FREQUENCY_ALL} | cut -d " " -f  $I`
        echo "${FREQUENCY[$I]}"
    done

    for i in $(seq 0 $CPU_NUM)
    do
       sleep 1
       ret=`cat /sys/bus/cpu/devices/cpu$i/cpufreq/scaling_cur_freq`
       if [ $? == 0  ]; then  
           echo "ret is $ret" 
           echo "FREQUENCY IS ${FREQUENCY[$N]}"	    
          if [ "${FREQUENCY[$N]}" = "$ret" ]; then
   	       let N=$N+1
	       echo "the frequency is same"
          fi
       fi

       echo userspace >/sys/bus/cpu/devices/cpu$i/cpufreq/scaling_governor
       if [ $? -ne 0 ]; then
            echo "<cpu_test>,<FAIL>,<-2>"
	    echo "<cpu_test>,<FAIL>,<-2>"
            sleep 1
            exit 2
       fi

       echo ${FREQUENCY[$N]} > /sys/bus/cpu/devices/cpu$i/cpufreq/scaling_setspeed 
  
       ret=`cat /sys/bus/cpu/devices/cpu$i/cpufreq/scaling_cur_freq`
       if [ $ret -eq ${FREQUENCY[$N]} ]; then
           echo "<cpu_test,CPUs ${TOTAL}>,<PASS>,<0>"
            sleep 1
	   exit 0
       fi
    done
fi

echo "<cpu_test>,<FAIL>,<-4>"
sleep 1
exit 1

