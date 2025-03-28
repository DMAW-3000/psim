"""
Serial communications devices
"""

import socket
import time
from threading import Thread, Lock

from pqueue import PQueue
        

class mc6850(object):
    """
    Motorolla 6850 serial device
    """
    
    def __init__(self, port, proc):
        self._proc = proc
        self._escape = ord('~')
        self._rx_data = 0x00
        self._status_reg = 0x02
        self._conn = SerialConnection(port)
        self._lock = Lock()
        self._tx_queue = PQueue(1)
        Thread(target = self._rx_wait).start()
        Thread(target = self._tx_wait).start()

    def size(self):
        return 2

    def write8(self, addr, value):
        if addr == 1:
            self._lock.acquire()
            self._status_reg &= 0xfd
            self._lock.release()
            #print("TX: %s" % chr(value))
            self._tx_queue.put(value)
            time.sleep(0.0)
        else:
            if (value & 0x03) == 0x03:
                #print("mc6850 reset")
                self._lock.acquire()
                self._rx_data = 0
                self._status_reg = 0x02
                self._lock.release()

    def _tx_wait(self):
        wr = self._conn.write
        lk = self._lock
        gf = self._tx_queue.get
        while True:
            x = gf(2.0)
            if x is None:
                if self._proc.halted():
                    return
            else:
                lk.acquire()
                self._status_reg |= 0x02
                lk.release()
                wr(x)

    def read8(self, addr):
        if addr == 1:
            self._lock.acquire()
            self._status_reg &= 0xfe
            x = self._rx_data
            self._lock.release()
            return x
        else:
            return self._status_reg

    def _rx_wait(self):
        rd = self._conn.read
        lk = self._lock
        es = self._escape
        while True:
            try:
                c = rd()
                if c == es:
                    self._proc.halt()
                    return
                lk.acquire()
                self._rx_data = c
                self._status_reg |= 0x01
                lk.release()
            except socket.timeout:
                if self._proc.halted():
                    return


class i8251(object):
    """
    Intel 8251 serial device
    """
    
    def __init__(self, port, proc):
        self._proc = proc
        self._escape = ord('~')
        self._rx_data = 0x00
        self._status_reg = 0x05
        self._mode_sel = True
        self._rx_enable = False
        self._tx_enable = False
        self._conn = SerialConnection(port)
        self._lock = Lock()
        self._tx_queue = PQueue(1)
        Thread(target=self._rx_wait).start()
        Thread(target=self._tx_wait).start()

    def size(self):
        return 2

    def write8(self, addr, value):
        if addr == 0:
            if self._mode_sel or (not self._tx_enable):
                #print("i8251 not enabled")
                return
            self._lock.acquire()
            self._status_reg &= 0xfa
            self._lock.release()
            #print("TX: %s" % chr(value))
            self._tx_queue.put(value)
            time.sleep(0.0)
        else:
            if self._mode_sel:
                if not (value & 0x03):
                    raise RuntimeError("i8251 sync mode not supported")
                #print("i8251 async mode")
                self._mode_sel = False
            else:
                if value & 0x40:
                    #print("i8251 reset")
                    self._rx_enable = False
                    self._tx_enable = False
                    self._mode_sel = True
                else:
                    self._tx_enable = (value & 0x01) != 0x00
                    self._rx_enable = (value & 0x04) != 0x00
                    #print("i8251 enable", self._tx_enable, self._rx_enable)

    def _tx_wait(self):
        gf = self._tx_queue.get
        wr = self._conn.write
        lk = self._lock
        while True:
            value = gf(2.0)
            if value is None:
                if self._proc.halted():
                    return
            else:
                lk.acquire()
                self._status_reg |= 0x05
                lk.release()
                wr(value)

    def read8(self, addr):
        if addr == 0:
            self._lock.acquire()
            self._status_reg &= 0xfd
            x = self._rx_data
            self._lock.release()
            return x
        else:
            return self._status_reg

    def _rx_wait(self):
        rd = self._conn.read
        lk = self._lock
        es = self._escape
        while True:
            try:
                c = rd()
                if c == es:
                    self._proc.halt()
                    return
                if self._rx_enable:
                    lk.acquire()
                    self._rx_data = c
                    self._status_reg |= 0x02
                    lk.release()
            except socket.timeout:
                if self._proc.halted():
                    return
                    
                    
class ns8250(object):

    def __init__(self, port, proc):
        self._proc = proc
        self._rbr = 0x00
        self._ier = 0x00
        self._iir = 0x01
        self._lcr = 0x00
        self._mcr = 0x00
        self._lsr = 0x60
        self._msr = 0xb0
        self._dll = 0x00
        self._dlm = 0x00
        self._scratch = 0x00
        self._escape = 0xff
        self._conn = SerialConnection(port)
        self._lock = Lock()
        Thread(target=self._rx_wait).start()
        
    def size(self):
        return 8
        
    def _rx_wait(self):
        while True:
            try:
                c = self._conn.read()
                #print("nc8250 rx %02x" % c)
                if c == self._escape:
                    self._proc.halt()
                    return
                self._rbr = c
                self._lock.acquire()
                self._lsr |= 0x01
                self._lock.release()
            except socket.timeout:
                if self._proc.halted():
                    return
        
    def read8(self, addr):
        #print("ns8250 rd %02x" % addr)
        if addr == 0:
            if (self._lcr & 0x80) == 0x00:
                self._lock.acquire()
                self._lsr &= 0xfe
                self._lock.release()
                return self._rbr
            else:
                return self._dll
        elif addr == 1:
            if (self._lcr & 0x80) == 0x00:
                return self._ier
            else:
                return self._dlm
        elif addr == 2:
            return self._iir
        elif addr == 3:
            return self._lcr
        elif addr == 4:
            return self._mcr
        elif addr == 5:
            return self._lsr
        elif addr == 6:
            return self._msr
        elif addr == 7:
            return self._scratch
        return 0x00
        
    def write8(self, addr, value):
        #print("ns8250 wr %02x %02x" % (addr, value))
        if addr == 0:
            if (self._lcr & 0x80) == 0x00:
                self._lock.acquire()
                self._lsr &= 0x9f
                self._lock.release()
                #print("TX: %s" % chr(value))
                self._conn.write(value)
                Thread(target = self._tx_wait).start()
            else:
                self._dll = value
        elif addr == 1:
            if (self._lcr & 0x80) == 0x00:
                self._ier = value
            else:
                self._dlm = value
        elif addr == 3:
            self._lcr = value
        elif addr == 4:
            self._mcr = value
        elif addr == 5:
            self._lsr = value
        elif addr == 6:
            self._msr = value
        elif addr == 7:
            self._scratch = value
            
    def _tx_wait(self):
        self._lock.acquire()
        self._lsr |= 0x60
        self._lock.release()

        
class SerialConnection(object):
    
    def __init__(self, port):
        self._tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rx_sock.bind(('', port + 1))
        self._rx_sock.settimeout(2.0)
        self._tx_addr = ('127.0.0.1', port)
        self._tx_buf = bytearray(1)
        
    def write(self, value):
        self._tx_buf[0] = value
        self._tx_sock.sendto(self._tx_buf, self._tx_addr)
        
    def read(self):
        return int((self._rx_sock.recvfrom(1)[0])[0])
