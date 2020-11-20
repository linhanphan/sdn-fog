# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 21:49:06 2019

@author: linhan
"""

import sys
import os
import numpy as np

config_dir = r'config_8'

for i in range(1, 101):
    np.random.seed(i)
    cpu = np.random.randint(low=25, high=80, size=8)
    ram = np.random.randint(low=250, high=800, size=8)
    hdd = np.random.randint(low=25, high=80, size=8)
    bw = np.random.randint(low=15, high=50, size=8)
    overload_node = np.random.randint(low=1, high=8, size=1)[0]
    f = open(config_dir + '/' + str(i), "w")
    f.write("Node_CPU" + " " + " ".join(map(str, cpu)) + "\n")
    f.write("Node_RAM" + " " + " ".join(map(str, ram)) + "\n")
    f.write("Node_HDD" + " " + " ".join(map(str, hdd)) + "\n")
    f.write("Node_BW" + " " + " ".join(map(str, bw)) + "\n")
    f.write("Overload_Node" + " " + str(overload_node) + "\n")
    f.close()
