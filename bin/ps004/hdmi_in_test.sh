#!/bin/bash

connect_status=`cat /sys/class/hdmirxswitch/hdmi/status | grep -a vid_locked |awk '{print  $3}'`

if [ $connect_status == "1" ]; then

	amixer -c mt8395evk cset name='HDMI_OUT_MUX' 1
	amixer -c mt8395evk cset name='DPTX_OUT_MUX' 1
	aplay -D hdmi_dp_out /home/root/xpcba/bin/ps004/test.wav &
	sleep 3
	audio_status=`cat /sys/class/hdmirxswitch/hdmi/status | grep -a aud |awk '{print  $3}'`

	if [ $audio_status == "1" ]; then
		echo "<hdmi_in_test>,<PASS>,<0>"
		exit 0
	else
		echo "<hdmi_in_audio_test>,<FAILT>,<-1>"
		exit 0
	fi
else
echo "<hdmi1_test_$fenbianlv>,<FAILT>,<-2>"
fi