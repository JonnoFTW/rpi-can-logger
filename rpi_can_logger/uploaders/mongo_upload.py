#!/usr/bin/env python3
from __future__ import print_function
import pymongo
import yaml
import json
from glob import glob
import os
from datetime import datetime
from dateutil.parser import parse
from io import StringIO

from rpi_can_logger.util import get_serial, get_ip

with open('./mongo_conf.yaml', 'r') as conf_fd:
    conf = yaml.load(conf_fd)

mongo_uri = conf['mongo_uri']
mongo_database = conf['mongo_database']
mongo_collection = conf['mongo_collection']
log_dir = conf['log_dir']
client = pymongo.MongoClient(mongo_uri, w=0)
rpi_readings_collection = client[mongo_database][mongo_collection]
rpi_info = client[mongo_database]['rpi-info']

serial = get_serial()
info = {'ip': get_ip(), 'ts': datetime.now(), 'serial': serial}

print(yaml.dump(info, default_flow_style=False))
rpi_info.delete_many({'serial': serial})
rpi_info.insert_one(info)
# start putting everything we've seen in the db


for fname in sorted(glob(log_dir + '/*.json')):
    if not os.access(fname, os.W_OK):
        print("Can't import {}, currently in use".format(fname))
    # make sure this file isn't open by another process
    trip_id = os.path.split(fname)[-1].split('.')[0]

    print("Importing", trip_id)

    with open(fname, 'r') as data_fh:
        all_data = data_fh.read().replace('\x00', '')
    all_data_fh = StringIO(all_data)
    del all_data

    rows = []
    row_count = 0
    for line in all_data_fh.getvalue().splitlines():
        try:
            row_obj = json.loads(line)
            if row_obj.get('timestamp') is not None:
                try:
                    row_obj['timestamp'] = parse(row_obj['timestamp'])
                except:
                    pass
            if row_obj.get('pos') is not None and not all(row_obj['pos']['coordinates']):
                # ignore invalid gps fields, don't skip because they might have gps turned off or something
                del row_obj['pos']
            row_count += 1
            rows.append(row_obj)
        except json.JSONDecodeError as e:
            print(e)

    if len(rows):
        try:
            rpi_readings_collection.remove({'trip_id': trip_id})
            rpi_readings_collection.insert_many(rows, ordered=False)
            # delete the file
            os.remove(fname)
        except Exception as e:
            print("Err", e)



