#!/bin/bash
number_of_sim=100
#repeat=(6 7 30 33 50 68 84)
mode="SDN"
echo "Total Number of Simulations : $number_of_sim"
echo "Start Running Simulation"
mn -c &> clear.txt
#clear
mv result "result_$(date +'%Y%m%d_%H%M%S')"
mv mininet_log "mininet_log_$(date +'%Y%m%d_%H%M%S')"
mkdir result
mkdir mininet_log

for (( counter=1; counter<$number_of_sim+1; counter++ ))
#for counter in ${repeat[@]}
do
echo "Start Simulation #$counter"
sleep 1
python topo.py $counter $mode &> mininet_log/$counter.txt
finish_file="result/$counter/done.txt"
while :
do
if [ -f "$finish_file" ]; then
    echo "Finish Simulation #$counter"
    break
else
    sleep 1
fi
done
sleep 1
mn -c &> clear.txt
mn -c &> clear.txt
#killall iperf
#killall -9 iperf
done

mv result "result_$(date +'%Y%m%d_%H%M%S')"
mv mininet_log "mininet_log_$(date +'%Y%m%d_%H%M%S')"
chmod -R 777 resul*
chmod -R 777 mininet_lo*
