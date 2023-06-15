import socket
import pickle
import time

from enum import Enum
from typing import Union, Dict, AnyStr

from device_controller import TX2Controller
from utils import set_logging

class Status(str, Enum):

    SENT="SENT"
    RECEIVED="RECEIVED"
        

class Server(object):

    def __init__(self, address='localhost', port=5634, name="server", verbose=True) -> None:
        self.logger = set_logging(name=name, filename=name, verbose=verbose)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((address, port))
        self.server_socket.listen(5)
        self.client_socket, self.address = self.server_socket.accept()
        self.logger.info(f"Connect to {self.client_socket.getsockname()}")
        
        self._initiate()
        

    def _initiate(self):
        self._recv_buffer = b''
        self._handshake_message()
        self._recv_message = None

    def _clean_recv_buffer(self):
        self._recv_buffer = b''

    def _clean_recv_message(self):
        self._recv_message = None

    def _handshake_message(self):
        self.send("Handshake from server")
        self.recv()

    def send(self, message: Union[Dict[str, str], AnyStr]):
        dumps_message = pickle.dumps(message)
        self.client_socket.send(dumps_message)
        self.logger.debug(f"[{Status.SENT}]: {message}")
        return self.recv()        

    def recv(self):
        self._recv()
        recv_message = self._recv_message
        self.logger.debug(f"[{Status.RECEIVED}]: {recv_message}")
        self._clean_recv_message()
        self._clean_recv_buffer()
        return recv_message
    
    def _recv(self, bufsize=8096):
        self._recv_buffer += self.client_socket.recv(bufsize)
        try:
            self._recv_message = pickle.loads(self._recv_buffer)
            return 
        except pickle.UnpicklingError:
            self._recv()

    def close(self):
        self.send('close')
        time.sleep(0.1)
        

class Client(object):
    
    def __init__(self, address='localhost', port=5634, name="client") -> None:
        self.logger = set_logging(name=name, filename=name)
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.client_socket.connect((address, port))
            except ConnectionRefusedError:
                self.logger.warning("Failed to connect. Please execute server end. Try again in 5 seconds...")
                time.sleep(5)
            else:
                break
        self.logger.info(f"Connect to {self.client_socket.getsockname()}")
        self.device_controller = TX2Controller()
        self._initiate()
        

    def _initiate(self):
        self._recv_buffer = b''
        self._handshake_message()
        self._recv_message = None
        
    def _handshake_message(self):
        self.send("Handshake from client")
    
    def _clean_recv_buffer(self):
        self._recv_buffer = b''
    
    def _clean_recv_message(self):
        self._recv_message = None

    def run(self):
        self._run()

    def _run(self):
        recv_message = self.recv()
        action = self.__placeholder(recv_message)
        self.send(action)
        if recv_message == "close":
            return self.close()
        self._run()

    def __placeholder(self, message):
        if message == 'action':
            return "test info"
        elif isinstance(message, dict):
            self.logger.debug(f"set specs {message}")
            self.device_controller.specs = message
            return 
        elif message == 'get_specs':
            return self.device_controller.specs
        else:
            return '√'
        

    def send(self, message: Union[Dict, AnyStr]):
        dumps_message = pickle.dumps(message)
        self.client_socket.send(dumps_message)
        self.logger.info(f"[{Status.SENT}]: {message}")
        
        
    def recv(self):
        self._recv()
        recv_message = self._recv_message
        self.logger.info(f"[{Status.RECEIVED}]: {recv_message}")
        self._clean_recv_message()
        self._clean_recv_buffer()
        return recv_message
    
    def _recv(self, bufsize=8096):
        self._recv_buffer += self.client_socket.recv(bufsize)
        try:
            self._recv_message = pickle.loads(self._recv_buffer)
            return 
        except pickle.UnpicklingError:
            self._recv()

    def close(self):
        self.device_controller._reset()
        self.logger.info("Close")
        