#!/bin/bash
#iperf3 -s -i 1 -p $((4000+$1)) -f k
iperf3 -s -i 1 -p $((4000+$1)) -f k --forceflush | stdbuf --output=L sed -r 's/.+ +([0-9]+) +.+\/sec.*$/\1/' > $HOME/iperf/server$1.speed
#  --forceflush | stdbuf --output=L
