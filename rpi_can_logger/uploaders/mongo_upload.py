#!/usr/bin/env python3
import pymongo
import yaml
from glob import glob
import csv
import os

with open('./mongo_conf.yaml', 'r') as conf_fd:
    conf = yaml.load(conf_fd)

mongo_uri = conf['mongo_uri']
mongo_database = conf['mongo_database']
mongo_collection = conf['mongo_collection']
log_dir = conf['log_dir']
client = pymongo.MongoClient(mongo_uri, w=0)

rpi_readings_collection = client[mongo_database][mongo_collection]

# start putting everything we've seen in the db
for fname in glob(log_dir+'/*.csv'):
    with open(fname, 'r') as data_fh:
        reader = csv.DictReader(data_fh)
        trip_id = os.split(fname)[-1].split('.')[0]
        rpi_readings_collection.remove({'trip_id': trip_id})
        print("Importing", trip_id)
        for row in reader:
            to_insert = {'trip_id': trip_id}
            to_insert.update(row)
            rpi_readings_collection.insert_one(to_insert)
    # delete the file
    os.remove(fname)

