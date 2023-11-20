#!/bin/bash

fenbianlv=`sed -n '2p' /sys/class/drm/card0-DP-1/modes`

if [ $fenbianlv == "3840x2160" ]; then
	echo "<DP_4K_test>,<PASS>,<0>"
	exit 0
fi
echo "<DP_test_$fenbianlv>,<FAILT>,<-1>"
