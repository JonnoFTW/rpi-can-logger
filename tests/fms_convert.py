#!/usr/bin/env python3
from rpi_can_logger.logger import fms_name2pid, fms_pids
import re
import sys
import yaml
import csv

with open(sys.argv[1], 'r') as infile:
    lines = infile.readlines()[17:]

read = set()
err = set()
not_from_std = set()
with open('../example_fms_logging.yaml', 'r') as conf:
    conf = yaml.load(conf)
filters = conf['log-pids']
# filters = fms_name2pid.keys()
print("Filtering:")
for i in filters:
    print("\t", hex(fms_name2pid[i]), i)
filters = set([fms_name2pid[i] for i in filters])
flatten = lambda l: [item for sublist in l for item in sublist]

with open(sys.argv[1] + '_2.csv', 'w') as outcsv:
    headers = flatten([fms_pids[f]['fieldnames'] for f in filters])
    headers = ['ts'] + headers
    writer = csv.DictWriter(outcsv, fieldnames=headers)
    writer.writeheader()
    lc = 0
    buf = {}
    for line in lines:
        pieces = re.split(r'\s+', line.strip())
        pid = (int("0x{}".format(pieces[3]), 16) >> 8) & 0xffff
        msg = bytes(map(lambda x: int(x, 16), pieces[5:]))
        lc += 1
        # if pieces[3] in ['1CEBFF01', '1CECFF01', '1CFDD101']:
        #     print(pieces[3], '\t', msg, '\t\t\t', ','.join(pieces[5:]))
        # continue
        if pid not in fms_pids:
            not_from_std.add(pieces[3])
            # print(lc, hex(int("0x" + pieces[3], 16)), msg, ', '.join([hex(i) for i in msg]))
        else:
            # try:
                parsed = fms_pids[pid]['parse'](msg)
                if pid in filters:
                    # pass
                    # print(pieces[0], fms_pids[pid]['name'], parsed)
                    parsed['ts'] = pieces[0][:-1]
                    buf.update(parsed)
                if fms_pids[pid]['name'] == conf['log-trigger']:
                    writer.writerow(buf)

                read.add(pid)
            # except Exception as e:
            #     print("Err on pid:", fms_pids[pid]['name'],pid, e)
            #     err.add(pid)

    for s in [('read', read), ('err', err), ('non_std', not_from_std)]:
        print(s[0])
        for ss in sorted(s[1]):
            if ss in fms_pids:
                print("\t", hex(ss), end=' ')
                print(fms_pids[ss]['name'])
            else:
                print("\t", ss)
