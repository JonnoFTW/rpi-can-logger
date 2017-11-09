#from setuptools import setup
import subprocess
import os
from glob import glob
import sys
if len(sys.argv) < 2:
    exit("Please specify a config file")
conf = sys.argv[1]
version = map(int, (0, 0, 1))
with open('requirements.txt', 'r') as reqs:
    requires = reqs.readlines()

# setup(
#     name='RPI-CAN-Logger',
#     version=','.join(version),
#     install_requires=requires,
#     description='Program to Log CAN bus and GPS data on a Raspberry Pi'
# )

for fname in glob('./systemd/*.service'):
    # modify the systemd service to replace {{pwd}}
    service_fname = fname # './systemd/rpi-logger.service'
    service = os.path.split(service_fname)[-1]
    print("Installing", service_fname)
    with open(service_fname, 'r') as service_fd:
        txt = service_fd.read()

    txt = txt.replace('{{pwd}}', os.getcwd())
    txt = txt.replace('{{conf}}', conf)
    print(txt)
    service_dir = '/lib/systemd/system/'
    service_fname_dest = service_dir + service

    with open(service_fname_dest, 'w') as service_fd:
        print("Writing to", service_fd.name)
        service_fd.write(txt)

    for i in [
        ['/usr/bin/sudo', 'chmod', '644', service_fname_dest],
        ['/usr/bin/sudo', 'systemctl', 'daemon-reload'],
        ['/usr/bin/sudo', 'systemctl', 'enable', service],

    ]:
        print(i, subprocess.check_output(i))
# modify /etc/systemd/system/dbus-org.bluez.service
# to use bluetoothd -C
with open('/etc/systemd/system/dbus-org.bluez.service','r') as btservice:
    btservicetxt = btservice.read()
    btservicetxt = btservicetxt.replace('ExecStart=/usr/lib/bluetooth/bluetoothd\n',
                                        'ExecStart=/usr/lib/bluetooth/bluetoothd -C\n')
with open('/etc/systemd/system/dbus-org.bluez.service','w') as btservice:
    btservice.write(btservicetxt)
