import netifaces as ni
from glob import glob


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
