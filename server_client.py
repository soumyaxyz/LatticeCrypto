import socket
# from _thread import *
from _thread import start_new_thread
import signal
import threading
import json, numpy as np
from abc import ABC, abstractmethod

class ServerClient():
    def __init__(self, port= 8080, parallel_incomming =1, name = 'Server'):
        self.port = port
        self.address = None
        self.name = name
        self.N = parallel_incomming
        self.print_lock = threading.Lock()
        self.message_size = 16   # bytes

        pass

    @abstractmethod
    def message_processing(self, msg, src_addr):
        pass

   

    def send_message(self, destination, msg):
        with socket.socket() as s:
            s.connect((destination[0], int(destination[1])))

            msg_json = json.dumps(msg).encode()
            msg_len = len(msg_json).to_bytes(self.message_size, byteorder='big')

            s.sendall(msg_len)
            s.sendall(msg_json)



    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf:
                return None
            buf += newbuf
            count -= len(newbuf)
        return buf

    def threaded(self, conn, addr):
        try:
            print(f"Connection {self.counter + 1} from {addr} accepted.")
            
            while True:
                data_len_bytes = self.recvall(conn, self.message_size)
                if not data_len_bytes:
                    break
                
                data_len = int.from_bytes(data_len_bytes, 'big')
                data_bytes = self.recvall(conn, data_len)
                if not data_bytes:
                    break

                data = json.loads(data_bytes.decode())
                self.message_processing(data, addr)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()
            self.counter += 1  # Increment the counter when a connection terminates

    def listen(self):
        s = socket.socket()

        s.bind(('', self.port))
        s.listen(self.N)

        print('{self.name} is listening at port {self.port}')

        signal.signal(signal.SIGINT, self.signal_handler)

        self.counter = self.N
        while self.counter >0 :
            conn, addr = s.accept()
            self.counter -= 1
            start_new_thread(self.threaded, (conn, addr))

    def listen(self):
        s = socket.socket()
        s.bind(('', self.port))
        s.listen(self.N)

        print(f'{self.name} is listening at port {self.port}')

        # Register a signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)

        for _ in range(self.N):
            conn, addr = s.accept()
            start_new_thread(self.threaded, (conn, addr))

    def signal_handler(self, signal, frame):
        print("Ctrl+C pressed. {self.name} terminated.")
        exit(0)  # Terminate the server gracefully
