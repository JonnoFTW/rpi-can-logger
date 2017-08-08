#!/usr/bin/env python3
from __future__ import print_function
import pymongo
import yaml
from glob import glob
import csv
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
vin_fallback = conf['vin_fallback']
rpi_readings_collection = client[mongo_database][mongo_collection]
rpi_info = client[mongo_database]['rpi-info']

serial = get_serial()
info = {'ip': get_ip(), 'ts': datetime.now(), 'serial': serial}

print(yaml.dump(info, default_flow_style=False))
rpi_info.delete_many({'serial': serial})
rpi_info.insert_one(info)
# start putting everything we've seen in the db


def convert(val):
    if type(val) not in [str, type(None)]:
        return val
    if val == '':
        return None
    try:
        if '.' in val:
            return float(val)
    except ValueError:
        pass
    try:
        return int(val)
    except ValueError:
        return val


for fname in sorted(glob(log_dir + '/*.csv')):
    # make sure this file isn't open by another process
    first_row = True
    trip_id = os.path.split(fname)[-1].split('.')[0]

    print("Importing", trip_id)

    with open(fname, 'r') as data_fh:
        all_data = data_fh.read().replace('\x00', '')
    all_data_fh = StringIO(all_data)
    del all_data

    reader = csv.DictReader(all_data_fh)
    rpi_readings_collection.remove({'trip_id': trip_id})
    # read up all the docs
    rows = []
    vid = vin_fallback
    row_count = 0
    for row in reader:
        if first_row:
            first_row = False
            if 'vid' in row and row['vid'] != 'False':
                vid = row['vid']
            else:
                print("Using fallback vin: {}".format(vid))
            continue
        to_insert = {'trip_id': trip_id, 'vid': vid, 'trip_sequence': row_count, 'pos': None}
        row_count += 1
        del row['vid']
        if row['latitude'] is not None and row['longitude'] is not None:
            try:
                row['pos'] = {
                    'type': 'Point',
                    'coordinates': [float(row['longitude']), float(row['latitude'])]
                }
            except:
                pass
        del row['latitude']
        del row['longitude']
        row = {k: convert(v) for k, v in row.items()}
        if row['timestamp'] is not None:
            try:
                row['timestamp'] = parse(row['timestamp'])
            except:
                pass
        
        to_insert.update(row)
        
#        print(to_insert)
        rows.append(to_insert)
    if len(rows):
        rpi_readings_collection.insert_many(rows, ordered=False)
    # delete the file
    
    os.remove(fname)
