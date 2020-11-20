#!/bin/bash

sim_id=(1 2)
overloadNode=(9 7)
offloadingNode=(13 5)

#for i in "${sim_id[@]}"
for (( i=0; i<10; i++ ))
do
    #mn -c &> clear.txt

    echo "Simulation :" ${sim_id[$i]}
    echo "overloadNode: " ${overloadNode[$i]}
    echo "offloadingNode: " ${offloadingNode[$i]}
    echo
    
    python topo_test_qos.py ${sim_id[$i]} ${overloadNode[$i]} ${offloadingNode[$i]}
    finish_file="result_QoS/$counter/result.txt"
    while :
    do
    if [ -f "$finish_file" ]; then
        sleep 1
	echo "Finish Simulation #$counter"
    	break
    else
    	sleep 1
    fi
    done
    sleep 1
    echo "Finish run topo and delete mininet topo"
    ovs-vsctl --all destroy QoS
    ovs-vsctl --all destroy Queue
    mn -c &> clear.txt
    mn -c &> clear.txt
    killall -9 nc
    killall -9 iperf
    sudo pkill -fx 'nc -k -l 12345'
    sleep 5
done
