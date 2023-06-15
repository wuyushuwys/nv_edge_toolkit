import logging
from collections import namedtuple, OrderedDict

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


decode = lambda res: res.stdout.decode('utf-8').split()[0]


Device_Specs = namedtuple('device', ['CPU', 'GPU', 'FAN'])
CPU_Specs = namedtuple('CPU', ['gov', 'freq', 'temp'])
GPU_Specs = namedtuple('GPU', ['gov', 'freq', 'temp'])
FAN_Specs = namedtuple('FAN', ['speed', 'temp'])

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


def set_logging(name, filename=None, verbose=False):
    # sets up logging for the given name
    logger = logging.getLogger(name)
    if logger.hasHandlers(): return logger 
    fh_formatter = logging.Formatter(fmt="%(asctime)s.%(msecs)03d::%(levelname)s::%(message)s",
                                     datefmt="%Y/%m/%d[%H:%M:%S]")
    ch_formatter = logging.Formatter(fmt="%(asctime)s.%(msecs)03d::%(message)s",
                                     datefmt="%Y/%m/%d[%H:%M:%S]")
    
    logger.setLevel(logging.INFO if verbose else logging.ERROR)
    
    ch = logging.StreamHandler()

    ch.setLevel(level=logging.INFO if verbose else logging.ERROR)
    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)
    
    fh = logging.FileHandler(filename=filename if filename else f"{name}.log",
                             mode='w')
    fh.setLevel(level=logging.DEBUG)
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    return logger