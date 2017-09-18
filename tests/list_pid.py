#!/usr/bin/env python3
from rpi_can_logger.logger import obd_name2pid
import yaml
import os
print(os.getcwd())
data = yaml.load(open('../example_obd_querying_conf.yaml', 'r'))
for pid_name in data['log-pids']:
    print ("e.set_pid(\"0{}\", 32)".format(hex(obd_name2pid[pid_name])[2:]))
