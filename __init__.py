from .device_controller import TX2Controller, CPU, GPU
from .socket_tools import Server, Client
from .utils import set_logging

IP_ADDR="192.168.55.100"
PORT=5634

__all__ = [
    'TX2Controller',
    'Server',
    'Client',
    'IP_ADDR',
    'PORT',
    'set_logging',
]