#!/usr/bin/env python3
from __future__ import print_function
import pymongo
import yaml
from glob import glob
import csv
import os
from datetime import datetime

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
for fname in sorted(glob(log_dir + '/*.csv'))[:-1]:
    # make sure this file isn't open by another process
    first_row = True
    with open(fname, 'r') as data_fh:
        reader = csv.DictReader(data_fh)
        trip_id = os.path.split(fname)[-1].split('.')[0]
        rpi_readings_collection.remove({'trip_id': trip_id})
        # read up all the docs
        print("Importing", trip_id)
        rows = []
        vid = serial
        for row in reader:
            if first_row:
                if 'vid' in row:
                    vid = row['vid']
                first_row = False
            to_insert = {'trip_id': trip_id, 'vid': vid}
            to_insert.update(row)
            rows.append(to_insert)
        rpi_readings_collection.insert_many(rows, ordered=False)
    # delete the file
    os.remove(fname)
