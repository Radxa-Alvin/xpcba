#!/bin/bash

amixer -c mt8395evk cset name='HDMI_OUT_MUX' 1
amixer -c mt8395evk cset name='DPTX_OUT_MUX' 1
aplay -D hdmi_dp_out test.wav &

fenbianlv=`sed -n '2p' /sys/class/drm/card0-HDMI-A-1/modes`

if [ $fenbianlv == "3840x2160" ]; then
	echo "<hdmi1_4K_test>,<PASS>,<0>"
	exit 0
fi
echo "<hdmi1_test_$fenbianlv>,<FAILT>,<-1>"
