"""
General purpose I/O devices
"""

import threading


class i8255(object):
    """
    Intel 8255 PIO device
    """
    
    def __init__(self, portIn = None, portOut = None):
        self._port_in = portIn
        self._port_out = portOut
        self._port_read = [True, True, True, True]
        
    def size(self):
        return 4
        
    def read8(self, addr):
        if (addr <= 1):
            if self._port_in is not None:
                if self._port_read[addr]:
                    return self._port_in(addr) & 0xff
        elif addr == 2:
            if self._port_in is not None:
                if self._port_read[2]:
                    n0 = self._port_in(2) & 0x0f
                else:
                    n0 = 0x00
                if self._port_read[3]:
                    n1 = self._port_in(3) & 0x0f
                else:
                    n1 = 0x00
                return (n1 << 4) | n0
        return 0x00
                
    def write8(self, addr, value):
        if (addr <= 1):
            if self._port_out is not None:
                if not self._port_read[addr]:
                    self._port_out(addr, value)
        elif addr == 2:
            if self._port_out is not None:
                if not self._port_read[2]:
                    self._port_out(2, value & 0x0f)
                if not self._port_read[3]:
                    self._port_out(3, (value >> 4) & 0x0f)
        else:
            #print("i8255 control %02x" % value)
            if not (value & 0x80):
                raise RuntimeError("i8255 bit set feature not supported")
            else:
                if ((value & 0x60) >> 5) == 2:
                    raise RuntimeError("i8255 bi-directional port A not supported")
                self._port_read[0] = (value & 0x10) != 0x00
                self._port_read[1] = (value & 0x02) != 0x00
                self._port_read[2] = (value & 0x01) != 0x00
                self._port_read[3] = (value & 0x08) != 0x00
                
                
                
class mc6820(object):
    """
    Motoralla 6820 PIA device
    """
    
    def __init__(self, portIn = None, portOut = None):
        self._port_in = portIn
        self._port_out = portOut
        self._cntl_reg_a = 0x00
        self._cntl_reg_b = 0x00
        self._dir_reg_a = 0x00
        self._dir_reg_b = 0x00
        self._out_reg_a = 0x00
        self._out_reg_b = 0x00
        self._lock = threading.Lock()
        
    def size(self):
        return 4
        
    def read8(self, addr):
        #print("mc6820 rd %04x" % addr)
        if addr == 0:
            if self._cntl_reg_a & 0x04:
                if self._port_in is not None:
                    mi = (~self._dir_reg_a) & 0xff
                    x = (self._port_in(0) & mi) | \
                        (self._out_reg_a & self._dir_reg_a)
                    self._lock.acquire()
                    self._cntl_reg_a &= 0x7f
                    self._lock.release()
                    return x
                else:
                    return 0xff
            else:
                return self._dir_reg_a
        elif addr == 1:
            return self._cntl_reg_a
        elif addr == 2:
            if self._cntl_reg_b & 0x04:
                if self._port_in is not None:
                    mi = (~self._dir_reg_b) & 0xff
                    x = (self._port_in(1) & mi) | \
                        (self._out_reg_b & self._dir_reg_b)
                    self._lock.acquire()
                    self._cntl_reg_b &= 0x7f
                    self._lock.release()
                    return x
                else:
                    return 0xff
            else:
                return self._dir_reg_b
        else:
            return self._cntl_reg_b
        
    def write8(self, addr, value):
        #print("mc6820 wr %04x %02x" % (addr, value))
        if addr == 0:
            if self._cntl_reg_a & 0x04:
                if self._port_out is not None:
                    value &= self._dir_reg_a
                    self._port_out(0, value)
                    self._out_reg_a = value
            else:
                self._dir_reg_a = value
        elif addr == 1:
            self._lock.acquire()
            self._cntl_reg_a |= (value & 0x3f)
            self._lock.release()
        elif addr == 2:
            if self._cntl_reg_b & 0x04:
                if self._port_out is not None:
                    value &= self._dir_reg_b
                    self._port_out(1, value)
                    self._out_reg_b = value
            else:
                self._dir_reg_b = value
        else:
            self._lock.acquire()
            self._cntl_reg_b |= (value & 0x3f)
            self._lock.release()
            
    def strobe(self, port):
        self._lock.acquire()
        if port == 0:
            self._cntl_reg_a |= 0x80
        elif port == 1:
            self._cntl_reg_b |= 0x80
        self._lock.release()
