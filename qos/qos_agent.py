#!/usr/bin/python

import sys
import os
import time
import subprocess
import socket
import select

output_dir = r'result_QoS'
sim = 0
node = 0
over_node = 0
off_node = 0
result_log = ''


def execute(result_log):
    num_test = 3
    if node == over_node:
        print 'over node', over_node
        # start test 1- data transfering
        while True:
            if os.path.isfile(rsPath + '/qos_test1'):
                break
            else:
                time.sleep(0.1)
        time.sleep(2)
        print "Start test 1-data transfering"
        for mb in ['50', '100', '200']:
            #file_name = str(mb)+'MB.bin'
            cmd = '/usr/bin/time -f \'%e\' dd if=/dev/zero bs=1M count=' + \
                str(mb) + ' | nc -q 0 10.0.0.' + str(off_node) + ' 5555'
            print cmd
            transfer_time = 0
            for i in range(0, num_test):
                while True:
                    if os.path.isfile(rsPath + '/' + mb + '_' + str(i)):
                        print "Found"
                        break
                    else:
                        #print "Not found"
                        time.sleep(1)

                print "Transfering " + str(mb) + ' MB #' + str(i + 1)
                time.sleep(0.1)
                start = time.time()
                log = os.system(cmd)
                print "LOGGGG", log
                end = time.time()
                print 'transfer_time ', (end - start)
                # if i > 0:
                transfer = float(end - start)
                transfer_time += (end - start)
                result_log += 'Time_Data_' + \
                    str(mb) + ' time ' + str(i) + ' ' + str(transfer) + '\n'
                time.sleep(10)
            result_log += 'Aver Time_Data_' + \
                str(mb) + ' ' + str(transfer_time / num_test) + '\n'
            print "Average transfering time of ", mb, ' MB :', transfer_time / \
                (num_test)
            time.sleep(10)
        log_file = open(rsPath + '/result.txt', "w+")
        log_file.write(result_log)
        log_file.close()
    else:
        print 'off_load node', off_node
        print "Start test case 1 "
        test_file = open(rsPath + '/qos_test1', "w+")
        test_file.close()
        #os.system('nc -k -l 30000 > /dev/null')

        for mb in ['50', '100', '200']:
            for i in range(0, num_test):
                test_file = open(rsPath + '/' + mb + '_' + str(i), "w+")
                os.system('nc -l -k 5555 > /dev/null')
                test_file.close()
                time.sleep(5)


if __name__ == '__main__':
    global sim
    global node
    global over_node
    global off_node
    global result_log
    result_log += 'Simalation ' + str(sim) + '\n'
    sim = int(sys.argv[1])
    node = int(sys.argv[2])
    over_node = int(sys.argv[3])
    off_node = int(sys.argv[4])
    print "sim, node, over_node, off_node", sim, node, over_node, off_node
    rsPath = str(output_dir + '/' + str(sim))
    apiPath = str(output_dir + '/' + str(sim) + '/api')
    agentPath = str(output_dir + '/' + str(sim) + '/agent')
    execute(result_log)
