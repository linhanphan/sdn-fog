#!/usr/bin/python

import sys
import os
import time
import subprocess
import requests
import socket
import select


config_dir = r'config_8'
output_dir = r'result'
result_log = ''
out_path = ''

sim = -1
cpu = []
ram = []
hdd = []
bw = 10
overload_node = 1
offloading_node = 1
offloading_node_sdn = 1
# mode are NoSDN, SDN, SDNQoS
mode = 'SDN'

overload_node = 1
numPing = 3
communication_time = 0.0
calculation_time = 0.0
delivery_time = 0.0

cpu_total = 100
ram_total = 1000
bw_total = 100
numHost = 8

cpu_weight = 1.0
ram_weight = 1.0
bw_weight = 1.0  # just used for SDN
hop_weight = 1.0  # used for SDN


def PingTest():
    listIP = []
    for i in range(1, 9):
        ip = '10.0.0.' + str(i)
        listIP.append(ip)
    listDelay = []
    for i in range(len(listIP)):  # ping
        os.system(
            'ping -c ' +
            str(numPing) +
            ' ' +
            listIP[i] +
            '| grep time= > pingresult')
        os.system(
            'cp pingresult ' +
            output_dir +
            '/' +
            sim +
            '/pingResult/' +
            str(i))
        total = 0.0
        numP = 0
        with open('pingresult', 'r') as f:
            for line in f:
                #print line
                time = line.split(' ')[-2]
                num = float(time.split('=')[1])
                total = total + num
                numP += 1

        print total, numP
        if numP != 0:
            listDelay.append(total / numP)
    return listDelay


def calculateTraditionalWeight(cpu, ram, bw, overId, listDelay):
    #cpu,ram, bw, overId = getResource()
    print cpu
    totalDelay = sum(listDelay) - listDelay[overId - 1]  # do not care current
    #print 'totalDelay', totalDelay
    outputWeight = {}
    for i in range(0, numHost):
        cpuLoad = float(cpu[i]) / cpu_total
        ramLoad = float(ram[i]) / ram_total
        w = (1.0 - float(cpu[i]) / cpu_total) * cpu_weight + \
            (1.0 - float(ram[i]) / ram_total) * ram_weight
        print 'w = ', w
        outputWeight.update({i + 1: w})
    print outputWeight
    print overId
    outputWeight.pop(overId, None)  # delete the overloadNode
    print outputWeight
    return outputWeight


def findTheBestNode(cpu, ram, bw, overload_node):
    global offloading_node
    time.sleep(1)
    listDelay = PingTest()
    startTime = time.time()
    ListWeightedNode = calculateTraditionalWeight(
        cpu, ram, bw, overload_node, listDelay)

    #print ListWeightedNode

    sortedList = sorted(
        ListWeightedNode,
        key=lambda x: ListWeightedNode[x],
        reverse=True)  # sort dic by value
    print "Best Node: id ", sortedList[0], "\nvalue:", ListWeightedNode[sortedList[0]]
    calculation_time = time.time() - startTime  # second
    print calculation_time
    sortedListDelay = sorted(listDelay, reverse=True)
    communication_time = float(sortedListDelay[0])
    print listDelay
    print communication_time
    delivery_time = calculation_time * 1000 + communication_time  # ms
    print 'delivery time', delivery_time
    if overload_node % 2 == 1:
        if sortedList[0] == overload_node + 1:
            offloading_node = sortedList[1]
        else:
            offloading_node = sortedList[0]
    else:
        if sortedList[0] == overload_node - 1:
            offloading_node = sortedList[1]
        else:
            offloading_node = sortedList[0]
    print 'bestNode', offloading_node
    result = open(
        output_dir +
        '/' +
        sim +
        '/node/' +
        str(offloading_node),
        "w+")
    result.close()
    #os.system('echo bestNode: ' + str(bestNode) + ' delivery_time: ' + str(delivery_time) + '>>' + outputFile + '/log' + str(fig))


def main(argv):
    global cpu
    global ram
    global hdd
    global bw
    global overload_node
    global offloading_node
    global result_log
    global output_dir
    global sim
    global out_path

    sim = str(sys.argv[1])
    node = int(sys.argv[2])
    mode = str(sys.argv[3])
    print 'Simalation ', sim
    result_log += 'Simalation ' + str(sim) + '\n'

    time.sleep(node)
    if not os.path.exists(output_dir + '/' + sim):
        os.makedirs(output_dir + '/' + sim)
    if not os.path.exists(output_dir + '/' + sim + '/node'):
        os.makedirs(output_dir + '/' + sim + '/node')
    if not os.path.exists(output_dir + '/' + sim + '/node_sdn'):
        os.makedirs(output_dir + '/' + sim + '/node_sdn')
    if not os.path.exists(output_dir + '/' + sim + '/api'):
        os.makedirs(output_dir + '/' + sim + '/api')
    if not os.path.exists(output_dir + '/' + sim + '/agent'):
        os.makedirs(output_dir + '/' + sim + '/agent')
    if not os.path.exists(output_dir + '/' + sim + '/pingResult'):
        os.makedirs(output_dir + '/' + sim + '/pingResult')
    os.system('rm ' + output_dir + '/' + sim + '/node' + '/*')
    time.sleep(18 - node)

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
                result_log += 'Overloading_node ' + str(overload_node) + '\n'

    os.system('iperf -c 10.0.0.9 -u -p ' +
              str(10000 +
                  node) +
              ' -b ' +
              str(bw[node -
                     1] *
                  1000000) +
              ' -d -L ' +
              str(10000 +
                  node) +
              ' -t 6000 -i 1 > ' +
              output_dir +
              '/' +
              sim +
              '/agent/' +
              str(node) +
              '_bw.txt &')
    # waiting for the result from controller
    out_path = output_dir + '/' + sim + '/node'
    out_path_sdn = output_dir + '/' + sim + '/node_sdn'
    time.sleep(5)
    # start agent process
    # check if i am overloading node
    if node == overload_node:
        print "I am overloading node ", node
        print "Running mode: ", mode
        # No SDN mode
        time.sleep(5)
        findTheBestNode(cpu, ram, bw, overload_node)
        time.sleep(5)
        print "Test latency to all host"
        latency = []
        number_of_request = 5
        for h in range(1, (numHost + 1)):
            if node != h:
                latency = [h]
                print "Test latency to host", h
                url = 'http://10.0.0.' + str(h) + ':5000/user/Jass'
                for i in range(0, number_of_request):
                    start = time.time()
                    r = requests.get(url)
                    #print r.json()
                    end = time.time()
                    print "request #", i + 1, ' ', (end - start) * 1000
                    latency.append((end - start) * 1000)
                    time.sleep(5)
                result_log += 'Latency_host ' + \
                    " ".join(map(str, latency)) + '\n'
        print "finish latency test"
        api_file = open(output_dir + '/' + sim + '/api_done', "w+")
        api_file.write(result_log)

        # get result from controller
        while True:
            if not os.listdir(out_path_sdn):
                time.sleep(0.5)
            else:
                output = os.listdir(out_path_sdn)
                offloading_node_sdn = int(output[0])
                break

        if offloading_node == offloading_node_sdn:
            result_log += 'Duplicate result ' + str(mode) + '\n'
            print "offloading_node node ", offloading_node
        else:
            time.sleep(5)

            output = os.listdir(out_path)
            print output
            offloading_node = int(output[0])
            print "offloading_node node ", offloading_node
            result_log += 'Offloading_node ' + str(offloading_node) + '\n'
            result_log += 'Offloading_node_SDN ' + \
                str(offloading_node_sdn) + '\n'

            time.sleep(5)
            # start test 1 with NoSDN- data transfering
            while True:
                if os.path.isfile(output_dir + '/' + sim + '/test1_nosdn'):
                    break
                else:
                    time.sleep(0.5)
            time.sleep(2)
            print "start test 1-data transfering"
            for mb in [50, 100, 200]:
                #file_name = str(mb)+'MB.bin'
                cmd = '/usr/bin/time -f \'%e\' dd if=/dev/zero bs=1M count=' + \
                    str(mb) + ' | nc -q 0 10.0.0.' + str(offloading_node) + ' 30000'
                print cmd
                transfer_time = 0
                num_test = 2
                for i in range(0, num_test):
                    while True:
                        if os.path.isfile(
                                output_dir + '/' + sim + '/' + str(mb) + '_nosdn_' + str(i)):
                            break
                        else:
                            time.sleep(0.1)
                    print "transfering " + str(mb) + ' MB #' + str(i + 1)
                    time.sleep(0.1)
                    start = time.time()
                    os.system(cmd)
                    end = time.time()
                    print 'transfer_time ', (end - start)
                    transfer_time += (end - start)
                    time.sleep(10)
                result_log += 'Time_Data_NoSDN_' + \
                    str(mb) + ' ' + str(transfer_time / num_test) + '\n'
                print "aver transfering time (no sdn) of", mb, ' MB :', transfer_time / num_test
                time.sleep(10)

            print "finish no sdn test"
            nosdn_file = open(output_dir + '/' + sim + '/NoSDN', "w+")
            nosdn_file.write(result_log)
            time.sleep(1)
            print "start test 1-data transfering"
            while True:
                if os.path.isfile(output_dir + '/' + sim + '/test1_sdn'):
                    break
                else:
                    time.sleep(0.5)
            for mb in [50, 100, 200]:
                #file_name = str(mb)+'MB.bin'
                cmd = '/usr/bin/time -f \'%e\' dd if=/dev/zero bs=1M count=' + \
                    str(mb) + ' | nc -q 0 10.0.0.' + str(offloading_node_sdn) + ' 30000'
                print cmd
                transfer_time = 0
                num_test = 2
                for i in range(0, num_test):
                    while True:
                        if os.path.isfile(
                                output_dir + '/' + sim + '/' + str(mb) + '_sdn_' + str(i)):
                            break
                        else:
                            time.sleep(0.1)
                    print "transfering " + str(mb) + ' MB #' + str(i + 1)
                    time.sleep(0.1)
                    start = time.time()
                    os.system(cmd)
                    end = time.time()
                    print 'transfer_time ', (end - start)
                    transfer_time += (end - start)
                    time.sleep(10)
                result_log += 'Time_Data_SDN_' + \
                    str(mb) + ' ' + str(transfer_time / num_test) + '\n'
                print "aver transfering time (no sdn) of", mb, ' MB :', transfer_time / num_test
                time.sleep(10)
        # time.sleep(5)

        # write log file
        log_file = open(output_dir + '/' + sim + '/result.txt', "w+")
        log_file.write(result_log)
        log_file.close()
        done_file = open(output_dir + '/' + sim + '/done.txt', "w+")
        done_file.close()
    else:
        print "I am normal  node ", node
        print "Start api server"
        os.system(
            'nohup python api_server.py >> ' +
            output_dir +
            '/' +
            sim +
            '/api/' +
            str(node) +
            '_api_server.txt 2>&1 &')

        while True:
            if not os.listdir(out_path):
                time.sleep(0.5)
            else:
                output = os.listdir(out_path)
                offloading_node = int(output[0])
                break
        while True:
            if not os.listdir(out_path_sdn):
                time.sleep(0.5)
            else:
                output = os.listdir(out_path_sdn)
                offloading_node_sdn = int(output[0])
                break
        if offloading_node != offloading_node_sdn:
            # time.sleep(5)
            if node == offloading_node:
                print "I am offloading  node ", node
                #print "Start test case 2 "
                #os.system('nohup python api_server.py >> '+output_dir+'/'+sim+'/api/'+str(node)+'_api_server.txt 2>&1 &')
                time.sleep(2)
                while True:
                    if os.path.isfile(output_dir + '/' + sim + '/api_done'):
                        break
                    else:
                        time.sleep(0.5)
                print "Start test case 1 for NoSDN"
                test_file = open(output_dir + '/' + sim + '/test1_nosdn', "w+")
                test_file.close()
                #os.system('nc -k -l 30000 > /dev/null')

                for mb in ['50', '100', '200']:
                    for i in range(0, 2):
                        test_file = open(
                            output_dir + '/' + sim + '/' + mb + '_nosdn_' + str(i), "w+")
                        os.system('nc -l 30000 > /dev/null')
                        test_file.close()
                        time.sleep(5)
            else:
                while True:
                    if os.path.isfile(output_dir + '/' + sim + '/NoSDN'):
                        break
                    else:
                        time.sleep(0.5)
                print "Start test case 1 for SDN"
                test_file = open(output_dir + '/' + sim + '/test1_sdn', "w+")
                test_file.close()
                #os.system('nc -k -l 30000 > /dev/null')

                for mb in ['50', '100', '200']:
                    for i in range(0, 2):
                        test_file = open(
                            output_dir + '/' + sim + '/' + mb + '_sdn_' + str(i), "w+")
                        os.system('nc -l 30000 > /dev/null')
                        test_file.close()
                        time.sleep(5)


if __name__ == "__main__":
    main(sys.argv[1:])
