import requests
import csv
from io import StringIO
from glob import glob
import os
import yaml

from .mongo_upload import convert


with open('./mongo_conf.yaml', 'r') as conf_fd:
    conf = yaml.load(conf_fd)

# load up the csv files and upload them in a compressed way

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
