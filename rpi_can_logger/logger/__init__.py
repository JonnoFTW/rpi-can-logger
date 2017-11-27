from .tesla_pids import pids as tesla_pids
from .obd_pids import pids as obd_pids
from .fms_pids import pids as fms_pids
from .bustech_pids import pids as bustech_pids
from .outlander_pids import pids as outlander_pids
from .csvrotator import CSVLogRotator
from .jsonlogrotator import JSONLogRotator
from .loggers import QueryingOBDLogger, SniffingOBDLogger, TeslaSniffingLogger, FMSLogger, BustechLogger
from .bluetooth_logger import BluetoothLogger

obd_pids.update(outlander_pids)
tesla_name2pid = {y['name']: x for x, y in tesla_pids.items()}
obd_name2pid = {y['name']: x for x, y in obd_pids.items()}
fms_name2pid = {y['name']: x for x, y in fms_pids.items()}
bustech_name2pid = {y['name']: x for x, y in bustech_pids.items()}
