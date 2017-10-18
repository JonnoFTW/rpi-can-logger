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
with open(os.path.expanduser(conf['pid-file']), 'r') as pid:
    currently_logging_to = pathlib.Path(pid.read().strip())

for fname in sorted(glob(log_dir + '/*.json*')):
    if fname == currently_logging_to:
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
    b64_data = base64.encode(contents)
    print("Uploading", end="... ")
    res = requests.post(api_url, {'keys': ",".join(keys), 'data': b64_data})
    # should probably remove the file here upon success
    print("Done")
