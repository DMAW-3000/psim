"""
Altair 8080 system.

16 KB RAM           = 0x0000
 4 KB BASIC ROM     = 0xe000,  altbasic.hex
256 B LOAD ROM      = 0xfc00,  altbload.hex
256 B MON ROM       = 0xfd00,  altmon.hex

App Directory:
app_altair8800

Serial Ports:
1 - primary,   port 50000
2 - secondary, port 50008
3 - secondary, port 50016

To boot BASIC from ROM, at the monitor prompt enter 'J176000'.
"""

from cpu.i8080 import i8080
from memory import *

from dev.serial import mc6850 

import os

RAM_ADDR = 0x0000
RAM_SIZE = 0x4000

BASIC_ROM_ADDR = 0xe000
BASIC_ROM_SIZE = 0x1000

BLOAD_ROM_ADDR = 0xfc00
BLOAD_ROM_SIZE = 0x0100

MON_ROM_ADDR = 0xfd00
MON_ROM_SIZE = 0x0100

SER2_IO     = 0x06
SER0_IO     = 0x10
SER1_IO     = 0x12
FP_IO       = 0xff

APP_DIR = "app_altair8800"


class Altair_FrontPanel(object):

    def size(self):
        return 1

    def read8(self, addr):
        return 0x08

    def write8(self, addr, value):
        print("FP write %02x" % value)


class System(object):

    def __init__(self, args):
    
        if args.mem_log:
            self._mem = AddressSpace("mem.txt")
        else:
            self._mem = AddressSpace()
        if args.io_log:
            self._io = AddressSpace("io.txt")
        else:
            self._io = AddressSpace()

        self.proc = i8080(self._mem, self._io)
        
        for a in args.breaks:
            try:
                self.proc.add_break(int(a, 16))
            except ValueError:
                print("ERROR: bad format for break %s" % a)
                exit(-1)

        ram = RAM(RAM_SIZE)
        self._mem.add(RAM_ADDR, ram, "SRAM")

        basicRom = ROM(BASIC_ROM_SIZE, os.path.join(APP_DIR, "altbasic.hex"), BASIC_ROM_ADDR)
        self._mem.add(BASIC_ROM_ADDR, basicRom, "BROM")

        monRom = ROM(MON_ROM_SIZE, os.path.join(APP_DIR, "altmon.hex"), MON_ROM_ADDR)
        self._mem.add(MON_ROM_ADDR, monRom, "MROM")

        basicLoadRom = ROM(BLOAD_ROM_SIZE, os.path.join(APP_DIR, "altbload.hex"), BLOAD_ROM_ADDR)
        self._mem.add(BLOAD_ROM_ADDR, basicLoadRom, "LROM")

        self._ser0 = mc6850(50000, self.proc)
        self._io.add(SER0_IO, self._ser0, "SER0")
        self._ser1 = mc6850(50008, self.proc)
        self._io.add(SER1_IO, self._ser1, "SER1")
        self._ser2 = mc6850(50016, self.proc)
        self._io.add(SER2_IO, self._ser2, "SER2")

        self._fp = Altair_FrontPanel()
        self._io.add(FP_IO, self._fp, "FPIO")
        
        # write JMP instruction to monitor program in ROM
        # this will be executed after reset
        ram.write8(0, 0xc3)
        ram.write8(1, MON_ROM_ADDR & 0xff)
        ram.write8(2, MON_ROM_ADDR >> 8)
        
    def run(self):
        self.proc.run()
    

if __name__ == '__main__':

    from application import AppParser
       
    args = AppParser().parse()
    system = System(args).run()
    
    

    
