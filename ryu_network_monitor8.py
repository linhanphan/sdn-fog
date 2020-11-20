from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib import mac
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from collections import defaultdict
from ryu.lib import hub
from operator import attrgetter
from datetime import datetime
import sched
import time
from threading import Thread
import sys
import os

# switches
myswitches = []
# mymac[srcmac]->(switch, port)
mymac = {}
# adjacency map [sw1][sw2]->port from sw1 to sw2
adjacency = defaultdict(lambda: defaultdict(lambda: None))
datapath_list = {}

# timer
scheduler = sched.scheduler(time.time, time.sleep)

# fog nodes
f_nodes = []

# available node connect to switch
available_nodes = [8, 10, 12, 15]

# switch_connect_to_overload_node
overload_node = 14

# available current bandwidth
# [src,dst,bw]
available_bw = []

byte = defaultdict(lambda: defaultdict(lambda: None))
clock = defaultdict(lambda: defaultdict(lambda: None))
bw_used = defaultdict(lambda: defaultdict(lambda: None))
bw_available = defaultdict(lambda: defaultdict(lambda: None))
bw = defaultdict(lambda: defaultdict(lambda: None))

target_srcmac = "00:00:00:00:00:13"
target_dstmac = "00:00:00:00:00:06"

# adding by linhan
# { 1 : {2:[list switch]} }
path_db = {}

# { s1_s2 : 30}
current_bw = {}
max_bw = {}
mac_ip_mapping = {}
ip_mac_mapping = {}


def scheduleTask():
    # scheduler.enter(300,1,find_best_node(),())
    scheduler.enter(150, 1, find_best_node_v2, argument=('2', 'SDN'))
    scheduler.run()


def max_abw(abw, Q):
    max = float('-Inf')
    node = 1
    for v in Q:
        if abw[v] > max:
            max = abw[v]
            node = v
    return node


def get_path2(src, dst, first_port, final_port):
    global bw_available
    #print "Dijkstra's widest path algorithm"
    #print "src=",src," dst=",dst, " first_port=", first_port, " final_port=", final_port
    # available bandwidth
    if src == dst:
        return [(src, first_port, final_port)]
    abw = {}
    previous = {}
    for dpid in myswitches:
        abw[dpid] = float('-Inf')
        previous[dpid] = None
    abw[src] = float('Inf')
    Q = set(myswitches)
    #print "Q:", Q
    #print time.time()
    while len(Q) > 0:
        u = max_abw(abw, Q)
        Q.remove(u)
        #print "Q:", Q, "u:", u
        for p in myswitches:
            #link_abw = bw_available[str(u)][str(p)]
            #print "link_abw:", str(u),"->",str(p),":",link_abw, "kbps"
            if adjacency[u][p] is not None:
                link_abw = bw_available[str(u)][str(p)]
                #print "link_abw:", str(u),"->",str(p),":",link_abw, "kbps"
                available_bw.append([u, p, link_abw])
                #alt=max(abw[p], min(width[u], abw_between(u,p)))
                if abw[u] < link_abw:
                    tmp = abw[u]
                else:
                    tmp = link_abw
                if abw[p] > tmp:
                    alt = abw[p]
                else:
                    alt = tmp
                if alt > abw[p]:
                    abw[p] = alt
                    previous[p] = u
    #print "distance=", distance, " previous=", previous
    r = []
    p = dst
    r.append(p)
    q = previous[p]
    while q is not None:
        if q == src:
            r.append(q)
            break
        p = q
        r.append(p)
        q = previous[p]
    r.reverse()
    if src == dst:
        path = [src]
        # r.append((dst,first_port,final_port))
        # return r
    else:
        path = r
    # Now add the ports
    r = []
    in_port = first_port
    for s1, s2 in zip(path[:-1], path[1:]):
        out_port = adjacency[s1][s2]
        r.append((s1, in_port, out_port))
        in_port = adjacency[s2][s1]
    r.append((dst, in_port, final_port))
    # if src and dst in mac_ip_mapping.keys():
    return r


def minimum_distance(distance, Q):
    #print "minimum_distance() is called", " distance=", distance, " Q=", Q
    min = float('Inf')
    node = 0
    for v in Q:
        if distance[v] < min:
            min = distance[v]
            node = v
    return node


def get_path(src, dst, first_port, final_port):
    # Dijkstra's algorithm
    global myswitches, adjacency
    #print "Dijkstra's shortest path algorithm"
    #print "get_path is called, src=",src," dst=",dst, " first_port=", first_port, " final_port=", final_port
    distance = {}
    previous = {}
    for dpid in myswitches:
        distance[dpid] = float('Inf')
        previous[dpid] = None
    distance[src] = 0
    Q = set(myswitches)
    #print "Q=", Q
    while len(Q) > 0:
        u = minimum_distance(distance, Q)
        #print "u=", u
        Q.remove(u)
        #print "After removing ", u, " Q=", Q
        for p in myswitches:
            if adjacency[u][p] is not None:
                #print u, "--------",  p
                w = 1
                if distance[u] + w < distance[p]:
                    distance[p] = distance[u] + w
                    previous[p] = u
    #print "distance=", distance, " previous=", previous
    r = []
    p = dst
    r.append(p)
    q = previous[p]
    while q is not None:
        if q == src:
            r.append(q)
            break
        p = q
        r.append(p)
        q = previous[p]
    r.reverse()
    if src == dst:
        path = [src]
    else:
        path = r
    # Now add the ports
    r = []
    in_port = first_port
    for s1, s2 in zip(path[:-1], path[1:]):
        out_port = adjacency[s1][s2]
        r.append((s1, in_port, out_port))
        in_port = adjacency[s2][s1]
    r.append((dst, in_port, final_port))
    return r


class ProjectController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ProjectController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.topology_api_app = self
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        sim = str(sys.argv[1])
        #node = int(sys.argv[2])
        mode = str(sys.argv[2])
        print "Starting scheduler"
        # scheduler.enter(300,1,find_best_node,())
        # scheduler.run()
        background_thread = Thread(target=scheduleTask, args=())
        background_thread.start()
        global bw
        try:
            fin = open("bw.txt", "r")
            for line in fin:
                a = line.split()
                if a:
                    bw[str(a[0])][str(a[1])] = int(a[2])
                    bw[str(a[1])][str(a[0])] = int(a[2])
                    max_bw[a[0] + '-' + a[1]] = int(a[2])
                    max_bw[a[1] + '-' + a[0]] = int(a[2])
            fin.close()
        except IOError:
            print "make bw.txt ready"
        print "bw:", bw

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                #self.logger.debug('register datapath: %016x', datapath.id)
                #print 'register datapath:', datapath.id
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                #self.logger.debug('unregister datapath: %016x', datapath.id)
                #print 'unregister datapath:', datapath.id
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(3)

    def _request_stats(self, datapath):
        #self.logger.debug('send stats request: %016x', datapath.id)
        #print 'send stats request:', datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        global byte, clock, bw_used, bw_available
        #print time.time()," _port_stats_reply_handler"
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        for stat in sorted(body, key=attrgetter('port_no')):
            #print dpid, stat.port_no, stat.tx_packets
            for p in myswitches:
                if adjacency[dpid][p] == stat.port_no:
                    #print dpid, p, stat.port_no
                    if byte[dpid][p] > 0:
                        #print "an ",str(bw[str(dpid)][str(p)])
                        if byte[dpid][p] > stat.tx_bytes:
                            byte[dpid][p] = 0
                        #print str(dpid)," -> ",str(p)," : ",str(stat.tx_bytes)," - ", str(byte[dpid][p])," MBps", " time",str(time.time()-clock[dpid][p])
                        bw_used[dpid][p] = (
                            stat.tx_bytes - byte[dpid][p]) * 8 / (time.time() - clock[dpid][p]) / 1000
                        bw_available[str(dpid)][str(p)] = (
                            int(bw[str(dpid)][str(p)]) * 1000) - bw_used[dpid][p]
                        #print str(dpid),"->",str(p)," max :", bw[str(dpid)][str(p)]," Mbps"
                        if bw_available[str(dpid)][str(p)] / 1000 < 1:
                            current_bw[str(dpid) + '-' + str(p)] = 1
                        else:
                            current_bw[str(dpid) + '-' + str(p)
                                       ] = bw_available[str(dpid)][str(p)] / 1000
                            #current_bw[str(p)+'-'+str(dpid)] = bw_available[str(dpid)][str(p)]/1000
                            #print str(dpid),"->",str(p)," avail :",bw_available[str(dpid)][str(p)]/1000," Mbps"
                    byte[dpid][p] = stat.tx_bytes
                    clock[dpid][p] = time.time()

    # Handy function that lists all attributes in the given object
    def ls(self, obj):
        print("\n".join([x for x in dir(obj) if x[0] != "_"]))

    def add_flow(self, datapath, in_port, dst, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port, eth_dst=dst)
        inst = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY, instructions=inst)
        datapath.send_msg(mod)

    def install_path(self, p, ev, src_mac, dst_mac):
        #print "install_path is called"
        #print "p=", p, " src_mac=", src_mac, " dst_mac=", dst_mac
        '''
        if src_mac in mac_ip_mapping.keys() and dst_mac in mac_ip_mapping.keys():
            scr_name = mac_ip_mapping[src_mac].split('.')[-1]
            dst_name = mac_ip_mapping[dst_mac].split('.')[-1]
            print scr_name,'-->',dst_name,p
               #temp = {}
               #temp[dst_name] = p
            if scr_name not in path_db.keys():
                path_db[scr_name] = {dst_name:p}
            else:
                path_db[scr_name][dst_name] = p
        '''
        if src_mac not in path_db.keys():
            path_db[src_mac] = {dst_mac: p}
        else:
            path_db[src_mac][dst_mac] = p
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        for sw, in_port, out_port in p:
            #print src_mac,"->", dst_mac, "via ", sw, " in_port=", in_port, " out_port=", out_port
            match = parser.OFPMatch(
                in_port=in_port,
                eth_src=src_mac,
                eth_dst=dst_mac)
            actions = [parser.OFPActionOutput(out_port)]
            datapath = datapath_list[sw]
            inst = [
                parser.OFPInstructionActions(
                    ofproto.OFPIT_APPLY_ACTIONS,
                    actions)]
            mod = datapath.ofproto_parser.OFPFlowMod(
                datapath=datapath, match=match, idle_timeout=0, hard_timeout=0,
                priority=1, instructions=inst)
            datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        print "switch_features_handler is called"
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER)]
        inst = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=0, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        global target_srcmac, target_dstmac, out_port
        #print "packet_in event:", ev.msg.datapath.id, " in_port:", ev.msg.match['in_port']
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        #print "eth.ethertype=", eth.ethertype
        # avodi broadcast from LLDP
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        if eth.ethertype == ether_types.ETH_TYPE_IP or eth.ethertype == ether_types.ETH_TYPE_IPV6:
            ip = pkt.get_protocol(ipv4.ipv4)
            srcip = ip.src
            dstip = ip.dst
            #print "src=", src, " dst=", dst, "srcip=", srcip, " dstip=", dstip," type=", hex(eth.ethertype)
            ip_mac_mapping[srcip] = src
            ip_mac_mapping[dstip] = dst
            mac_ip_mapping[src] = srcip
            mac_ip_mapping[dst] = dstip

        #print "adjacency=", adjacency
        self.mac_to_port.setdefault(dpid, {})
        if src not in mymac.keys():
            mymac[src] = (dpid, in_port)
            #print "mymac=", mymac
        if dst in mymac.keys():
            p = get_path2(
                mymac[src][0],
                mymac[dst][0],
                mymac[src][1],
                mymac[dst][1])
            # build database of paths
            '''
          if src in mac_ip_mapping.keys() and dst in mac_ip_mapping.keys():
              scr_name = mac_ip_mapping[src].split('.')[-1]
              dst_name = mac_ip_mapping[dst].split('.')[-1]
              print scr_name,'-->',dst_name,p
              #temp = {}
              #temp[dst_name] = p
              if scr_name not in path_db.keys():
                  path_db[scr_name] = {dst_name:p}
              else:
                  path_db[scr_name][dst_name] = p
          '''
            #print "path = ",p
            # Adding fog nodes
            if mymac[src][0] == overload_node and mymac[dst][0] != overload_node:
                #print "path = ",p
                if mymac[dst][0] in available_nodes:
                    node = Fog_Node(str(mymac[src][0]) + ":" + str(mymac[dst][0]) + ":" + str(len(p)) + ":" + str(
                        calculate_bandwidth_with_path(p)), dst, len(p), True, calculate_bandwidth_with_path(p))
                    f_nodes.append(node)
            self.install_path(p, ev, src, dst)
            out_port = p[0][2]
        else:
            out_port = ofproto.OFPP_FLOOD
        actions = [parser.OFPActionOutput(out_port)]
        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        if out_port == ofproto.OFPP_FLOOD:
            #print "FLOOD"
            while len(actions) > 0:
                actions.pop()
            for i in range(1, 23):
                actions.append(parser.OFPActionOutput(i))
            #print "actions=", actions
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=msg.buffer_id,
                in_port=in_port,
                actions=actions,
                data=data)
            datapath.send_msg(out)
        else:
            #print "unicast"
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
                actions=actions, data=data)
            datapath.send_msg(out)
    events = [event.EventSwitchEnter,
              event.EventSwitchLeave, event.EventPortAdd,
              event.EventPortDelete, event.EventPortModify,
              event.EventLinkAdd, event.EventLinkDelete]

    @set_ev_cls(events)
    def get_topology_data(self, ev):
        #print "get_topology_data() is called"
        global myswitches, adjacency, datapath_list
        switch_list = get_switch(self.topology_api_app, None)
        myswitches = [switch.dp.id for switch in switch_list]
        for switch in switch_list:
            datapath_list[switch.dp.id] = switch.dp
        #print "datapath_list=", datapath_list
        print "myswitches=", myswitches
        links_list = get_link(self.topology_api_app, None)
        #print "links_list=", links_list
        mylinks = [
            (link.src.dpid,
             link.dst.dpid,
             link.src.port_no,
             link.dst.port_no) for link in links_list]
        for s1, s2, port1, port2 in mylinks:
            #print "type(s1)=", type(s1), " type(port1)=", type(port1)
            adjacency[s1][s2] = port1
            adjacency[s2][s1] = port2
            #print s1,":", port1, "<--->",s2,":",port2


def remove_duplicate_items(iterable):
    result = []
    for item in iterable:
        if item not in result:
            result.append(item)
    return result


def find_best_node():
    print 'Find best node:', time.time()
    print 'mac-ip', mac_ip_mapping
    print 'ip-mac', ip_mac_mapping
    start = time.time()
    f_nodes_sorted = sorted(f_nodes)
    f_nodes_show = [n.src_name for n in f_nodes_sorted]
    # remove duplicate
    result = []
    for item in f_nodes_show:
        if item not in result:
            result.append(item)
    print "Fog nodes = ", result, ":", time.time() - start


def find_best_node_v2(sim, mode):
    print 'Find best node v2 (linhan):', time.time()
    if(len(mac_ip_mapping.keys()) < 9):
        return
    number_of_sim = 100
    config_dir = r'config_8'
    output_dir = r'result'
    #rerun = [6,7,30,33,50,68,84,109]
    # for s in rerun:
    for si in range(1, 101):
        sim = str(si)
        print 'Simulation', sim
        while True:
            if os.path.exists(output_dir + '/' + sim):
                break
            else:
                time.sleep(2)
                print 'Waiting sim ', sim
                print 'bw used', bw_used
        while True:
            if os.path.isfile(output_dir + '/' + sim + '/init.txt'):
                break
            else:
                time.sleep(1)
        time.sleep(15)
        #print 'bw used', bw_used
        time.sleep(15)
        #print 'bw used', bw_used
        time.sleep(45)
        print 'bw used', bw_used
        print 'mac-ip', mac_ip_mapping
        print 'ip-mac', ip_mac_mapping
        print 'current bw', current_bw
        if si < 5:
            print 'path_db', path_db
        # for k in path_db.keys():
        #    print 'Path from',mac_ip_mapping[k].split('.')[-1]
        #    for l in path_db[k].keys():
        #        print mac_ip_mapping[k].split('.')[-1],'->',mac_ip_mapping[l].split('.')[-1],path_db[k][l]
        start = time.time()
        print "Read config file"
        #config_dir = r'config'
        #output_dir = r'result'
        overload_node = 1
        offloading_node = 1
        with open(config_dir + '/' + sim) as f:
            for line in f:
                if "Node_CPU" in line:
                    cpu = map(int, line.split()[1:])
                if "Node_RAM" in line:
                    ram = map(int, line.split()[1:])
                if "Node_HDD" in line:
                    hdd = map(int, line.split()[1:])
                if "Node_BW" in line:
                    bw = map(int, line.split()[1:])
                if "Overload_Node" in line:
                    overload_node = int(line.split()[-1])
                    print 'Overload_Node', overload_node

        cpu_total = 100
        ram_total = 1000
        bw_total = 100
        hop_total = 8
        numHost = 8
        req_cpu = 10
        req_ram = 100
        req_bw = 1
        min_ratio = 1.0
        cpu_weight = 1.0
        ram_weight = 1.0
        bw_weight = 1.0
        hop_weight = 1.0

        offloading_node = 0
        max_point = 0
        over_mac = ip_mac_mapping['10.0.0.' + str(overload_node)]
        dict_cpu = {}
        dict_ram = {}
        dict_bw = {}
        dict_hop = {}
        for i in range(0, numHost):
            if i != (overload_node - 1):
                mac_add = ip_mac_mapping['10.0.0.' + str(i + 1)]
                path_to_node = path_db[over_mac][mac_add]
                hop = len(path_to_node) + 1
                min_bw = 1000
                if hop == 2:
                    # this is neighboring node
                    hop = 8
                    min_bw = 0
                else:
                    # get min bw from list of links
                    for j in range(0, len(path_to_node) - 1):
                        free_bw = current_bw[str(
                            path_to_node[j][0]) + '-' + str(path_to_node[j + 1][0])]
                        if free_bw < min_bw:
                            min_bw = free_bw
                    dict_cpu[i + 1] = float(cpu_total - cpu[i]) / req_cpu
                    dict_ram[i + 1] = float(ram_total - ram[i]) / req_ram
                    dict_bw[i + 1] = float(min_bw) / req_bw
                    dict_hop[i + 1] = float(hop_total) / hop
                    print 'Node', i + \
                        1, 'cpu', dict_cpu[i + 1], 'ram', dict_ram[i + 1], 'bw', dict_bw[i + 1], 'hop', dict_hop[i + 1]
        print 'bw', dict_bw
        for k in dict_cpu.keys():
            cpu_nor = (dict_cpu[k] - min_ratio) / \
                (max(dict_cpu.values()) - min_ratio)
            ram_nor = (dict_ram[k] - min_ratio) / \
                (max(dict_ram.values()) - min_ratio)
            bw_nor = (dict_bw[k] - min_ratio) / \
                (max(dict_bw.values()) - min_ratio)
            hop_nor = (dict_hop[k] - min_ratio) / \
                ((hop_total / 2) - min_ratio)
            score = cpu_nor * cpu_weight + ram_nor * ram_weight + \
                bw_nor * bw_weight + hop_nor * hop_weight
            print 'Node', k, 'cpu', cpu_nor, 'ram', ram_nor, 'bw', bw_nor, 'hop', hop_nor
            print 'Node', k, 'score', score
            if score > max_point:
                max_point = score
                offloading_node = k
        print 'Final result Offloading_node', offloading_node, 'score', max_point
        print 'Write the result to file'
        if not os.path.exists(output_dir + '/' + sim + '/node_sdn'):
            os.makedirs(output_dir + '/' + sim + '/node_sdn')
        result = open(
            output_dir +
            '/' +
            sim +
            '/node_sdn/' +
            str(offloading_node),
            "w+")
        result.close()
        end = time.time()
        print 'Calculate time (ns)', (end - start) * 1000000
        while True:
            if os.path.isfile(output_dir + '/' + sim + '/done.txt'):
                print 'Finished sim ', sim
                break
            else:
                time.sleep(1)
        ip_mac_mapping.clear()
        mac_ip_mapping.clear()
        path_db.clear()
        current_bw.clear()
        byte.clear()
        clock.clear()
        bw_used.clear()
        bw_available.clear()


def find_bw(src, des):
    for item in available_bw:
        if item[0] == src and item[1] == des:
            return item[2]


def calculate_bandwidth_with_path(path):
    bandwidth_arr = []
    for x in range(0, len(path) - 1):
        bandwidth_arr.append(find_bw(path[x][0], path[x + 1][0]))
    return max(bandwidth_arr)


class Fog_Node(object):
    """Represent fog node"""

    def __init__(
            self,
            src_name,
            dst_name,
            hops_count,
            is_available,
            bandwidth_available):
        super(Fog_Node, self).__init__()
        self.src_name = src_name
        self.dst_name = dst_name
        self.hops_count = hops_count
        self.bandwidth_available = bandwidth_available
        self.is_available = is_available

    def __eq__(self, other):
        return self.bandwidth_available == other.bandwidth_available and self.hops_count == other.hops_count

    def __lt__(self, other):
        return self.bandwidth_available >= other.bandwidth_available and self.hops_count <= other.hops_count
