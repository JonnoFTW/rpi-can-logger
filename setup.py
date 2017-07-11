from setuptools import setup

version = map(int, (0, 0, 1))
with open('requirements.txt', 'r') as reqs:
    requires = reqs.readlines()

setup(
    name='RPI-CAN-Logger',
    version=','.join(version),
    install_requires=requires,
    description='Program to Log CAN bus and GPS data on a Raspberry Pi'
)

# TODO a function to install as a systemd service
