import logging
import os
from collections import namedtuple

__all__ = [
    'PASSWORD',
    'decode',
    'Device_Specs',
    'CPU_Specs',
    'GPU_Specs',
    'FAN_Specs',
    'set_logging',
    'parse_specs'
]


PASSWORD='nvidia'


decode = lambda res: eval(res.stdout.decode('utf-8').split()[0])


Device_Specs = namedtuple('device', ['CPU', 'GPU', 'FAN'])
Device_power_Specs = namedtuple('device', ['CPU', 'GPU', 'FAN', 'POWER'])
CPU_Specs = namedtuple('CPU', ['gov', 'freq', 'temp'])
GPU_Specs = namedtuple('GPU', ['gov', 'freq', 'temp'])
FAN_Specs = namedtuple('FAN', ['control', 'speed', 'temp'])


def parse_specs(specs):
    specs['CPU'] = CPU_Specs(**specs['CPU'])
    specs['GPU'] = GPU_Specs(**specs['GPU'])
    specs['FAN'] = FAN_Specs(**specs['FAN'])
    return specs


def encode_specs(specs: Device_Specs):
    dict_specs = specs._asdict()
    for k, v in dict_specs.items():
        dict_specs[k] = v._asdict()
    return dict_specs


def set_logging(name, verbose=False):
    # sets up logging for the given name
    logger = logging.getLogger(name)
    if logger.hasHandlers(): return logger 
    fh_formatter = logging.Formatter(fmt="%(asctime)s.%(msecs)03d::%(levelname)s::%(message)s",
                                     datefmt="%Y/%m/%d[%H:%M:%S]")
    ch_formatter = logging.Formatter(fmt="%(asctime)s.%(msecs)03d::%(message)s",
                                     datefmt="%Y/%m/%d[%H:%M:%S]")
    
    logger.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler()

    ch.setLevel(level=logging.INFO if verbose else logging.ERROR)
    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)

    dirname, _ = os.path.split(name)
    if dirname != '':
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

    
    fh = logging.FileHandler(filename=f"{name}.log",
                             mode='w')
    fh.setLevel(level=logging.DEBUG)
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    return logger