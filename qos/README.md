# Test Enabling QoS 

This is guideline to evaluate QoS feature in SDN-based network. Note that for QoS setting (queue in OVS), you need to run the simulation manually.

## Usage
You need two Terminal to run the simulation

```bash
# Terminal 1 for Controller 
sudo ryu-manager --observe rest_qos.py rest_conf_switch.py qos_simple_switch_13.py ryu_network_monitor16.py


# Terminal 2 for mininet
# Setup topology
sudo python topo_test_qos.py [SimulationID] [OverloadedNodeID] [OffloadingNodeID]
# sudo python topo_test_qos.py 1 9 13

# Access to overloaded and offloading nodes to test throughput
# In Mininet CLI 
xterm [OverloadedNodeID] [OffloadingNodeID]

# In Xterm screen of offloading node
nc -k -l 30000 > /dev/null
 
# In Xterm screen of overloaded node
/usr/bin/time -f %e dd if=/dev/zero bs=1M count=100 | nc -q 0 [OffloadingNode_IP] 5555

# Check queue
ovs-vsctl list queue

# Reset settings after finishing one simulation
ovs-vsctl --all destroy QoS
ovs-vsctl --all destroy Queue
```


## Contact
If you have any problem in running the scripts, please email me at linhan90 [at] gmail [.] com

