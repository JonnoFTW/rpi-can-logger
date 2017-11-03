#!/usr/bin/env python
import sys
import yaml
hostname = sys.argv[1]

# set the hostname of the device to be hostname
# set the config to use the appropriate hostname
for f in ['/etc/hosts', '/etc/hostname']:
    with open(f, 'r') as infile:
        text = infile.read()
    text = text.replace('rpi-logger-0', hostname)
    with open(f, 'w') as outfile:
        outfile.write(text)

bus_id = hostname.split("-")[-1]
conf = '/home/pi/rpi-can-logger/example_fms_logging.yaml'
with open(conf, 'r') as stream:
    try:
        data = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

with open(conf, 'w') as outstream:
    data['vehicle-id'] = data['vehicle-id'].replace('2450', bus_id)
    yaml.dump(data, outstream)

import subprocess