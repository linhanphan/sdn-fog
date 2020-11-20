#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
import time
import sys
import os

config_dir = r'config'
output_dir = r'result_QoS'
overLoadingNode = -1
offLoadingNode = -1


def myNetwork(sim):

    if not os.path.exists(output_dir + '/' + sim):
        os.makedirs(output_dir + '/' + sim)
    rsPath = str(output_dir + '/' + str(sim))
    if not os.path.exists(output_dir + '/' + sim + '/agent'):
        os.makedirs(output_dir + '/' + sim + '/agent')
    agentPath = str(output_dir + '/' + sim + '/agent')
    if not os.path.exists(output_dir + '/' + sim + '/iperf'):
        os.makedirs(output_dir + '/' + sim + '/iperf')
    iperfPath = str(output_dir + '/' + sim + '/iperf')

    net = Mininet(topo=None,
                  build=False,
                  ipBase='10.0.0.0/8')

    info('*** Adding controller\n')
    c0 = net.addController(name='c0',
                           controller=RemoteController,
                           ip='127.0.0.1',
                           port=6633)
    hosts = []
    switches = []
    #links = []
    info('*** Add switches\n')
    for i in range(1, 16):
        s = net.addSwitch('s' + str(i), cls=OVSKernelSwitch)
        switches.append(s)
        s.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        s.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        s.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
        s.cmd('ovs-vsctl set bridge s' + str(i) + ' protocols=OpenFlow13')
        s.cmd('ovs-vsctl set-manager ptcp:6632')
        #s.cmd('ovs-ofctl add-flow s'+str(i)+' "table=0, priority=0, actions=resubmit(,1)"')
        #s.cmd('ovs-ofctl add-flow s'+str(i)+' "table=1, priority=0, actions=CONTROLLER:65535"')

    info('*** Add hosts\n')
    for i in range(1, 18):
        h = net.addHost(
            'h' + str(i),
            cls=Host,
            ip='10.0.0.' + str(i),
            defaultRoute=None)
        hosts.append(h)
        h.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    info('*** Add links\n')

    h17s1 = {}
    net.addLink(hosts[16], switches[0], cls=TCLink, **h17s1)
    s2s1 = {}
    net.addLink(switches[1], switches[0], cls=TCLink, **s2s1)
    s3s1 = {}
    net.addLink(switches[2], switches[0], cls=TCLink, **s3s1)
    s4s2 = {}
    net.addLink(switches[3], switches[1], cls=TCLink, **s4s2)
    s5s2 = {}
    net.addLink(switches[4], switches[1], cls=TCLink, **s5s2)
    s6s3 = {}
    net.addLink(switches[5], switches[2], cls=TCLink, **s6s3)
    s7s3 = {}
    net.addLink(switches[6], switches[2], cls=TCLink, **s7s3)
    s8s4 = {}
    net.addLink(switches[7], switches[3], cls=TCLink, **s8s4)
    s9s4 = {}
    net.addLink(switches[8], switches[3], cls=TCLink, **s9s4)
    s10s5 = {}
    net.addLink(switches[9], switches[4], cls=TCLink, **s10s5)
    s11s5 = {}
    net.addLink(switches[10], switches[4], cls=TCLink, **s11s5)
    s12s6 = {}
    net.addLink(switches[11], switches[5], cls=TCLink, **s12s6)
    s13s6 = {}
    net.addLink(switches[12], switches[5], cls=TCLink, **s13s6)
    s14s7 = {}
    net.addLink(switches[13], switches[6], cls=TCLink, **s14s7)
    s15s7 = {}
    net.addLink(switches[14], switches[6], cls=TCLink, **s15s7)
    h1s8 = {}
    if offLoadingNode == 1:
        h1s8 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[0], switches[7], cls=TCLink, **h1s8)
    h2s8 = {}
    if offLoadingNode == 2:
        h2s8 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[1], switches[7], cls=TCLink, **h2s8)
    h3s9 = {}
    if offLoadingNode == 3:
        h3s9 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[2], switches[8], cls=TCLink, **h3s9)
    h4s9 = {}
    if offLoadingNode == 4:
        h4s9 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[3], switches[8], cls=TCLink, **h4s9)
    h5s10 = {}
    if offLoadingNode == 5:
        h5s10 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[4], switches[9], cls=TCLink, **h5s10)
    h6s10 = {}
    if offLoadingNode == 6:
        h6s10 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[5], switches[9], cls=TCLink, **h6s10)
    h7s11 = {}
    if offLoadingNode == 7:
        h7s11 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[6], switches[10], cls=TCLink, **h7s11)
    h8s11 = {}  # h5 is overload, h8 is offloading node
    if offLoadingNode == 8:
        h8s11 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[7], switches[10], cls=TCLink, **h8s11)
    h9s12 = {}
    if offLoadingNode == 9:
        h9s12 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[8], switches[11], cls=TCLink, **h9s12)
    h10s12 = {}
    if offLoadingNode == 10:
        h10s12 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[9], switches[11], cls=TCLink, **h10s12)
    h11s13 = {}
    if offLoadingNode == 11:
        h11s13 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[10], switches[12], cls=TCLink, **h11s13)
    h12s13 = {}
    if offLoadingNode == 12:
        h12s13 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[11], switches[12], cls=TCLink, **h12s13)
    h13s14 = {}
    if offLoadingNode == 13:
        h13s14 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[12], switches[13], cls=TCLink, **h13s14)
    h14s14 = {}
    if offLoadingNode == 14:
        h14s14 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[13], switches[13], cls=TCLink, **h14s14)
    h15s15 = {}
    if offLoadingNode == 15:
        h15s15 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[14], switches[14], cls=TCLink, **h15s15)
    h16s15 = {}
    if offLoadingNode == 16:
        h16s15 = {'bw': 100, 'delay': '1ms', 'loss': 0}
    net.addLink(hosts[15], switches[14], cls=TCLink, **h16s15)

    info('*** Starting network\n')
    net.build()
    info('*** Starting controllers\n')

    info('*** Starting switches\n')
    for s in switches:
        s.start([c0])
        time.sleep(1)

    info('*** Post configure switches and hosts\n')
    swid = -1
    pid = -1
    if overLoadingNode % 2 == 0:
        swid = overLoadingNode / 2 + 7
        pid1 = 3
        pid2 = 2
        noiseNegbor = overLoadingNode - 1
    else:
        swid = (overLoadingNode + 1) / 2 + 7
        pid1 = 2
        pid2 = 3
        noiseNegbor = overLoadingNode + 1

    if offLoadingNode % 2 == 0:
        swid_D = offLoadingNode / 2 + 7
    else:
        swid_D = (offLoadingNode + 1) / 2 + 7

    upSwid = swid_D / 2
    if swid_D % 2 == 0:
        upPort = 2
    else:
        upPort = 3

    minQueue0 = 0
    maxQueue0 = 30000000
    minQueue1 = 70000000
    maxQueue1 = 100000000
    # set new flow
    switches[swid - 1].cmd('./newflow.sh')
    net.pingAll()

    swidhex = '{:x}'.format(swid)
    upSwidhex = '{:x}'.format(upSwid)
    print "sw, upsw:", swidhex, upSwidhex
    cmd1 = "ovs-vsctl -- set port s{}-eth1 qos=@newqos -- --id=@newqos create qos type=linux-htb queues=0=@q0,1=@q1 -- --id=@q0 create queue other-config:min-rate=0 other-config:max-rate={} -- --id=@q1 create queue other-config:min-rate=0 other-config:max-rate={}".format(
        str(swid), str(maxQueue0), str(maxQueue1))
    print "cmd1", cmd1
    switches[swid - 1].cmd(cmd1)
    # switches[swid -
    #         1].cmd('curl -X POST -d \'{"port_name": "s' +
    #                str(swid) +
    #                '-eth1", "type": "linux-htb", "max_rate": "100000000", "queues": [{"min_rate": "10000000", "max_rate": "30000000"}, {"min_rate": "70000000","max_rate": "90000000"}]}\' http://localhost:8080/qos/queue/000000000000000' +
    #                str(swidhex))
    switches[swid -
             1].cmd('curl -X POST -d \'{"match": {"nw_dst": "10.0.0.' +
                    str(offLoadingNode) +
                    '", "nw_proto": "UDP", "tp_dst": "5555"}, "actions":{"queue": "1"}}\' http://localhost:8080/qos/rules/000000000000000' +
                    str(swidhex))
    switches[swid -
             1].cmd('curl -X POST -d \'{"match": {"nw_dst": "10.0.0.' +
                    str(offLoadingNode) +
                    '", "nw_proto": "TCP", "tp_dst": "5555"}, "actions":{"queue": "1"}}\' http://localhost:8080/qos/rules/000000000000000' +
                    str(swidhex))
    cmd2 = "ovs-vsctl -- set port s{}-eth{} qos=@newqos -- --id=@newqos create qos type=linux-htb queues=0=@q0,1=@q1 -- --id=@q0 create queue other-config:min-rate=0 other-config:max-rate={} -- --id=@q1 create queue other-config:min-rate=0 other-config:max-rate={}".format(
        str(upSwid),
        str(upPort),
        str(maxQueue0),
        str(maxQueue1))
    print "cmd2", cmd2
    switches[upSwid - 1].cmd(cmd2)
    # switches[upSwid -
    #         1].cmd('curl -X POST -d \'{"port_name": "s' +
    #                str(upSwid) +
    #                '-eth' +
    #                str(upPort) +
    #                '", "type": "linux-htb", "max_rate": "100000000", "queues": [{"min_rate": "10000000", "max_rate": "30000000"}, {"min_rate": "70000000","max_rate": "90000000"}]}\' http://localhost:8080/qos/queue/000000000000000' +
    #                str(upSwidhex))
    switches[upSwid -
             1].cmd('curl -X POST -d \'{"match": {"nw_dst": "10.0.0.' +
                    str(offLoadingNode) +
                    '", "nw_proto": "UDP", "tp_dst": "5555"}, "actions":{"queue": "1"}}\' http://localhost:8080/qos/rules/000000000000000' +
                    str(upSwidhex))
    switches[upSwid -
             1].cmd('curl -X POST -d \'{"match": {"nw_dst": "10.0.0.' +
                    str(offLoadingNode) +
                    '", "nw_proto": "TCP", "tp_dst": "5555"}, "actions":{"queue": "1"}}\' http://localhost:8080/qos/rules/000000000000000' +
                    str(upSwidhex))

    time.sleep(3)
    print("Open iperf server")
    #hosts[offLoadingNode - 1].cmd('iperf -s -u -D -p 5555 > log1.txt 2&1 &')
    hosts[offLoadingNode -
          1].cmd('iperf -s -u -D -i 1 -p 6666 > ' +
                 iperfPath +
                 '/log66_' +
                 str(sim) +
                 '.txt &')
    hosts[offLoadingNode -
          1].cmd('iperf -s -u -D -i 1 -p 7777 >  ' +
                 iperfPath +
                 '/log77_' +
                 str(sim) +
                 '.txt &')

    time.sleep(3)
    noiseId = 0
    for i in range(1, 16):
        if i != overLoadingNode and i != overLoadingNode:
            noiseId = i
            break
    print("Send traffic by iperf")
    #hosts[overLoadingNode - 1].cmd('iperf -c 10.0.0.' + str(offLoadingNode) +' -u -b 100M -t 800 -p 5555')
    hosts[noiseNegbor -
          1].cmd('iperf -c 10.0.0.' +
                 str(offLoadingNode) +
                 ' -u -b 50M -t 800 -p 6666 &')
    hosts[noiseId -
          1].cmd('iperf -c 10.0.0.' +
                 str(offLoadingNode) +
                 ' -u -b 50M -t 800 -p 7777 &')

    time.sleep(3)
    print("Open qos_agent.py by iperf")
    hosts[overLoadingNode -
          1].cmd('nohup python qos_agent2.py ' +
                 str(sim) +
                 ' ' +
                 str(overLoadingNode) +
                 ' ' +
                 str(overLoadingNode) +
                 ' ' +
                 str(offLoadingNode) +
                 ' > ' +
                 agentPath +
                 '/over_agent.txt &')
    #hosts[offLoadingNode-1].cmd('nohup python qos_agent.py ' + str(sim) + ' ' +str(offLoadingNode)+' '+str(overLoadingNode)+' '+ str(offLoadingNode)+' > ' + agentPath + '/offload_agent.txt &')
    hosts[offLoadingNode -
          1].cmd('nohup python qos_agent2.py ' +
                 str(sim) +
                 ' ' +
                 str(offLoadingNode) +
                 ' ' +
                 str(overLoadingNode) +
                 ' ' +
                 str(offLoadingNode) +
                 ' > ' +
                 agentPath +
                 '/offload_agent.txt &')
    CLI(net)

    time.sleep(2)
    print "Waiting result file"
    while True:
        if os.path.isfile(rsPath + '/result.txt'):
            break
        else:
            time.sleep(1)

    for h in hosts:
        h.cmd('killall -9 iperf')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')

    #global sim
    global overLoadingNode
    global offLoadingNode

    sim = str(sys.argv[1])
    #node = int(sys.argv[2])
    overLoadingNode = int(sys.argv[2])
    offLoadingNode = int(sys.argv[3])
    print sim, overLoadingNode, offLoadingNode

    myNetwork(sim)
