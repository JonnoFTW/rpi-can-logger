try:
    import netifaces as ni
except ImportError:
    ni = None
from glob import glob
import subprocess

OBD_REQUEST = 0x07DF
OBD_RESPONSE = 0x07E8


def get_serial():
    with open('/proc/cpuinfo', 'r') as cpu_info:
        return cpu_info.readlines()[-1].strip().split(' ')[-1]


def get_ip():
    try:
        return ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']
    except:
        return "ERROR"


def list_log(log_dir):
    return ", ".join(sorted(glob(log_dir + "/*.csv")))


def sudo(cmd):
    subprocess.call("/usr/bin/sudo bash -c '{}'".format(cmd), shell=True)
