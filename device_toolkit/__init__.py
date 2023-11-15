from .device_controller import TX2Controller, OrinNanoController
from .device_controller import TX2GPU, TX2CPU, OrinNanoGPU, OrinNanoCPU 
from .socket_tools import Server, Client
from .utils import set_logging

__version__ = "0.2.5"
__author__ = 'Yushu Wu'
__credits__ = 'Northeastern Univeristy, Boston, MA'

IP_ADDR="192.168.55.100"
PORT=5634

__all__ = [
    'TX2Controller',
    'OrinNanoController',
    'Server',
    'Client',
    'IP_ADDR',
    'PORT',
    'set_logging',
]