
from memory import RAM

from multiprocessing import shared_memory

class VRAM(object):

    def __init__(self, size, smName):
        self._size = size
        try:
            self._sm = shared_memory.SharedMemory(smName)
            self._buf = self._sm._buf
        except FileNotFoundError:
            self._sm = RAM(size)
            self._buf = self._sm._m

    def size(self):
        return self._size

    def read8(self, addr):
        return self._buf[addr]

    def write8(self, addr, value):
        self._buf[addr] = value

    def read16le(self, addr):
        buf = self._buf
        return (buf[addr + 1] << 8) + buf[addr]

    def write16le(self, addr, value):
        buf = self._buf
        buf[addr] = value & 0xff
        buf[addr + 1] = value >> 8
        

class mc6845(object):

    def __init__(self):
        try:
            self._sm = shared_memory.SharedMemory("VREG_6845")
            self._regs = self._sm._buf
        except FileNotFoundError:
            self._regs = bytearray(256)
        self._reg_addr = 0x00

    def size(self):
        return 2

    def write8(self, addr, value):
        #print("mc6845 wr %04x %02x" % (addr, value))
        if addr == 0:
            self._reg_addr = value
        else:
            self._regs[self._reg_addr] = value

    def read8(self, addr):
        print("mc6845 rd %04x" % addr)
        return 0x00