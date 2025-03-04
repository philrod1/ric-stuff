#!/bin/bash
url="http://localhost:3000/configs/test.json"
json=$(curl -s "$url")
count=$(echo "$json" | jq -r '.gnbs | length')
port=2000
device_args="fail_on_disconnect=true, id=enb, base_srate=23.04e6"
for ((i = 0; i < $count; i++)); do
    device_args="$device_args, tx_port$i=tcp://*:$((port+i)), rx_port$i=tcp://localhost:$((port+i+100))"
done
ricport=5006
srsenb                                                \
     --enb.n_prb=50                                   \
     --enb.name=enb                                   \
     --enb.enb_id=0x191                               \
     --rf.device_name=zmq                             \
     --rf.device_args="$device_args"                  \
     --ric.agent.remote_ipv4_addr="$E2TERM"           \
     --log.all_level=warn                             \
     --ric.agent.log_level=debug                      \
     --log.filename=stdout                            \
     --ric.agent.local_ipv4_addr="$myip"              \
     --ric.agent.local_port=$ricport
