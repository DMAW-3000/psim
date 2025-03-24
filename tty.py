"""
Terminal emulator.
"""


import socket
import msvcrt
import time
import threading
import sys


class Tty(object):

    def __init__(self, readPort):
        self._exit = False
        self._read_port = readPort
        self._write_port = readPort + 1
        self._write_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._read_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._read_sock.bind(('', self._read_port))
        self._read_sock.settimeout(1.0)

    def run(self):
        threading.Thread(target = self._read_thread).start()
        sendAddr = ('127.0.0.1', self._write_port)
        while True:
            #data = input()
            if msvcrt.kbhit():
                chars =  msvcrt.getch()
                for c in chars:
                    if c == ord('!'):
                        self._exit = True
                        return
                    elif c != ord('\n'):
                        self._write_sock.sendto(bytearray((c,)), sendAddr)
            time.sleep(0.1)


    def _read_thread(self):
        out = sys.stdout
        while True:
            try:
                (data, addr) = self._read_sock.recvfrom(1024)
                out.write(chr(data[0] & 0x7f))
                out.flush()
            except socket.timeout:
                pass
            finally:
                if self._exit:
                    return

        
if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("port", type=int)
    args = parser.parse_args()
    Tty(args.port).run()
    
    
    

    
