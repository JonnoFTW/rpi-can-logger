from setuptools import setup
import subprocess
import os
from glob import glob

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
    print("Installing", service_fname)
    with open(service_fname, 'r') as service_fd:
        txt = service_fd.read()

    txt.replace('{{pwd}}', os.getcwd())
    with open(service_fname, 'w') as service_fd:
        service_fd.write(txt)

    service_dir = '/lib/systemd/system/'
    service_fname_dest = service_dir + service_fname
    for i in [
        ['sudo', 'cp', '-f', service_fname, service_fname_dest],
        ['sudo', 'chmod', '644', service_fname_dest],
        ['sudo', 'systemctl', 'daemon-reload'],
        ['sudo', 'systemctl', 'enable', os.path.split(service_fname_dest)[-1]],

    ]:
        print(i, subprocess.check_output(i))
