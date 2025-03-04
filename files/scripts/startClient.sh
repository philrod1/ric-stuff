#!/bin/bash
ip netns exec ue$1 iperf3 -c 172.16.0.1 -u -b 1M -i 1 -t 1000 -p $((4000+$1))
