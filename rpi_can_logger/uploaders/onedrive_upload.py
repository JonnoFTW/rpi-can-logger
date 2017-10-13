#!/usr/bin/env python3
import onedrivesdk
from onedrivesdk.helpers import GetAuthCodeServer
import yaml
import requests
from rpi_can_logger.uploaders import is_connected

"""
This doesn't even work
"""
if not is_connected():
    exit('No internet connection')

# print("Net connection?", is_connected())
with open('../onedrive.yaml', 'r') as conf_fh:
    conf = yaml.load(conf_fh)

client_id = conf['client_id']
client_secret = conf['client_secret']
redirect_uri = 'http://localhost:8080'
scopes = ['offline_access', 'files.readwrite.all']

requests.get('https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
             params={'client_id': client_id,
                     'scope': ' '.join(scopes),
                     'response_type': 'code',
                     'redirect_uri': redirect_uri
                     })
pass
