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
filters = fms_name2pid.keys()
print("Filtering:")
for i in filters:
    print("\t", i, hex(fms_name2pid[i]))
filters = set([fms_name2pid[i] for i in filters])
flatten = lambda l: [item for sublist in l for item in sublist]
with open(sys.argv[1] + '.csv', 'w') as outcsv:
    headers = flatten([fms_pids[f]['fieldnames'] for f in filters])
    writer = csv.DictWriter(outcsv, fieldnames=headers)
    writer.writeheader()

    for line in lines:
        pieces = re.split(r'\s+', line.strip())
        pid = (int("0x{}".format(pieces[3]), 16) >> 8) & 0xffff
        msg = bytes(map(lambda x: int(x, 16), pieces[5:]))
        if pid not in fms_pids:
            not_from_std.add(pieces[3])
        else:
            try:
                parsed = fms_pids[pid]['parse'](msg)
                if pid in filters:
                    # print(fms_pids[pid]['name'], parsed)
                    writer.writerow(parsed)
                read.add(pid)
            except Exception as e:
                # print("Err on pid:", fms_pids[pid]['name'],pid, e)
                err.add(pid)

for s in [('read', read), ('err', err), ('non_std', not_from_std)]:
    print(s[0])
    for ss in sorted(s[1]):
        if ss in fms_pids:
            print("\t", hex(ss), end=' ')
            print(fms_pids[ss]['name'])
        else:
            print("\t", ss)
