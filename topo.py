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
output_dir = r'result'


def myNetwork(sim, mode):

    if not os.path.exists(output_dir + '/' + sim):
        os.makedirs(output_dir + '/' + sim)
    if not os.path.exists(output_dir + '/' + sim + '/node'):
        os.makedirs(output_dir + '/' + sim + '/node')
    if not os.path.exists(output_dir + '/' + sim + '/api'):
        os.makedirs(output_dir + '/' + sim + '/api')
    if not os.path.exists(output_dir + '/' + sim + '/agent'):
        os.makedirs(output_dir + '/' + sim + '/agent')

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
    '''
    s9 = net.addSwitch('s9', cls=OVSKernelSwitch)
    s10 = net.addSwitch('s10', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s11 = net.addSwitch('s11', cls=OVSKernelSwitch)
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch)
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s7 = net.addSwitch('s7', cls=OVSKernelSwitch)
    s12 = net.addSwitch('s12', cls=OVSKernelSwitch)
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s6 = net.addSwitch('s6', cls=OVSKernelSwitch)
    s13 = net.addSwitch('s13', cls=OVSKernelSwitch)
    s14 = net.addSwitch('s14', cls=OVSKernelSwitch)
    s15 = net.addSwitch('s15', cls=OVSKernelSwitch)
    s8 = net.addSwitch('s8', cls=OVSKernelSwitch)
    '''
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
    h17s1 = {'bw': 1000}
    net.addLink(hosts[16], switches[0], cls=TCLink, **h17s1)
    s2s1 = {'bw': 400, 'delay': '2ms'}
    net.addLink(switches[1], switches[0], cls=TCLink, **s2s1)
    s3s1 = {'bw': 400, 'delay': '2ms'}
    net.addLink(switches[2], switches[0], cls=TCLink, **s3s1)
    s4s2 = {'bw': 200, 'delay': '2ms'}
    net.addLink(switches[3], switches[1], cls=TCLink, **s4s2)
    s5s2 = {'bw': 200, 'delay': '2ms'}
    net.addLink(switches[4], switches[1], cls=TCLink, **s5s2)
    s6s3 = {'bw': 200, 'delay': '2ms'}
    net.addLink(switches[5], switches[2], cls=TCLink, **s6s3)
    s7s3 = {'bw': 200, 'delay': '2ms'}
    net.addLink(switches[6], switches[2], cls=TCLink, **s7s3)
    s8s4 = {'bw': 100, 'delay': '2ms'}
    net.addLink(switches[7], switches[3], cls=TCLink, **s8s4)
    s9s4 = {'bw': 100, 'delay': '2ms'}
    net.addLink(switches[8], switches[3], cls=TCLink, **s9s4)
    s10s5 = {'bw': 100, 'delay': '2ms'}
    net.addLink(switches[9], switches[4], cls=TCLink, **s10s5)
    s11s5 = {'bw': 100, 'delay': '2ms'}
    net.addLink(switches[10], switches[4], cls=TCLink, **s11s5)
    s12s6 = {'bw': 100, 'delay': '2ms'}
    net.addLink(switches[11], switches[5], cls=TCLink, **s12s6)
    s13s6 = {'bw': 100, 'delay': '2ms'}
    net.addLink(switches[12], switches[5], cls=TCLink, **s13s6)
    s14s7 = {'bw': 100, 'delay': '2ms'}
    net.addLink(switches[13], switches[6], cls=TCLink, **s14s7)
    s15s7 = {'bw': 100, 'delay': '2ms'}
    net.addLink(switches[14], switches[6], cls=TCLink, **s15s7)
    h1s8 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[0], switches[7], cls=TCLink, **h1s8)
    h2s8 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[1], switches[7], cls=TCLink, **h2s8)
    h3s9 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[2], switches[8], cls=TCLink, **h3s9)
    h4s9 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[3], switches[8], cls=TCLink, **h4s9)
    h5s10 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[4], switches[9], cls=TCLink, **h5s10)
    h6s10 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[5], switches[9], cls=TCLink, **h6s10)
    h7s11 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[6], switches[10], cls=TCLink, **h7s11)
    h8s11 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[7], switches[10], cls=TCLink, **h8s11)
    h9s12 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[8], switches[11], cls=TCLink, **h9s12)
    h10s12 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[9], switches[11], cls=TCLink, **h10s12)
    h11s13 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[10], switches[12], cls=TCLink, **h11s13)
    h12s13 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[11], switches[12], cls=TCLink, **h12s13)
    h13s14 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[12], switches[13], cls=TCLink, **h13s14)
    h14s14 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[13], switches[13], cls=TCLink, **h14s14)
    h15s15 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[14], switches[14], cls=TCLink, **h15s15)
    h16s15 = {'bw': 100, 'delay': '1ms'}
    net.addLink(hosts[15], switches[14], cls=TCLink, **h16s15)

    info('*** Starting network\n')
    net.build()
    info('*** Starting controllers\n')

    info('*** Starting switches\n')
    for s in switches:
        s.start([c0])
        time.sleep(1)
    '''
    net.get('s9').start([c0])
    net.get(switches[9]).start([c0])
    net.get('switches[2]').start([c0])
    net.get('s11').start([c0])
    net.get('switches[3]').start([c0])
    net.get('s1').start([c0])
    net.get('s7').start([c0])
    net.get('s12').start([c0])
    net.get('s5').start([c0])
    net.get('switches[1]').start([c0])
    net.get('s6').start([c0])
    net.get('s13').start([c0])
    net.get('s14').start([c0])
    net.get('s15').start([c0])
    net.get('s8').start([c0])
    '''

    info('*** Post configure switches and hosts\n')

    net.pingAll()

    for p in range(10001, 10017):
        hosts[-1].cmd('iperf -s -u -D -p ' + str(p))

    for i in range(1, 17):
        if True:
            hosts[i -
                  1].cmd('nohup python fog_agent.py ' +
                         sim +
                         ' ' +
                         str(i) +
                         ' ' +
                         mode +
                         ' > result/' +
                         sim +
                         '/agent/' +
                         str(i) +
                         '_agent.txt &')

    # CLI(net)
    time.sleep(2)
    init_done = open(output_dir + '/' + sim + '/init.txt', "w+")
    init_done.close()
    while True:
        if os.path.isfile(output_dir + '/' + sim + '/done.txt'):
            break
        else:
            time.sleep(1)
    for i in range(0, 17):
        hosts[i].cmd('killall iperf')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    sim = str(sys.argv[1])
    #node = int(sys.argv[2])
    mode = str(sys.argv[2])
    myNetwork(sim, mode)
