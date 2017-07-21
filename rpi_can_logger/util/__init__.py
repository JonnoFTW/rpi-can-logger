import netifaces as ni


def get_serial():
    with open('/proc/cpuinfo', 'r') as cpu_info:
        return cpu_info.readlines()[-1].strip().split(' ')[-1]


def get_ip():
    return ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']
