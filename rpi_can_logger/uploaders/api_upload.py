import requests
from glob import glob
import os
import base64
import yaml
import gzip
import pathlib

with open('./mongo_conf.yaml', 'r') as conf_fd:
    conf = yaml.load(conf_fd)

log_dir = conf['log_dir']
keys = conf['keys']
api_url = conf['api_url']+'upload'
try:
    with open(os.path.expanduser(conf['pid-file']), 'r') as pid:
        currently_logging_to = pathlib.Path(pid.read().strip())
except:
    currently_logging_to = ''
for fname in sorted(glob(log_dir + '/*.json*')):
    if fname.endswith('.done'):
        os.rename(fname, fname[:-5])
    if fname == currently_logging_to or fname.endswith('.done'):
        continue
    print("Importing", fname)

    with open(fname, 'rb') as ingz:
        contents = ingz.read()
    if fname.endswith('.json'):
        # compress that file!
        contents = gzip.compress(contents)
    if not contents:
        print("Removing empty file")
        os.remove(fname)
        continue
    b64_data = base64.b64encode(contents)
    print("Uploading", end="... ")
    res = requests.post(api_url, {'keys': ",".join(keys), 'data': b64_data})
    print(res)
    # should probably remove the file here upon success
    if res.status_code == requests.codes.ok:
        os.rename(fname, fname+'.done')
        print("Done")
    else:
        print("Error uploading: {}".format(res.text))

