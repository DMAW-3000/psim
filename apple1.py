"""
Apple 1 system.

 8 KB RAM           = 0x0000
256 B MON ROM       = 0xff00,  wozmon.hex

"""

from cpu.m6502 import m6502
from memory import *


import os

RAM_ADDR = 0x0000
RAM_SIZE = 0x4000

WOZ_ROM_ADDR = 0xff00
WOZ_ROM_SIZE = 0x0100

APP_DIR = "app_apple1"



class Apple1_System(object):

    def __init__(self, args):
    
        if args.mem_log:
            self._mem = AddressSpace("mem.txt", not args.debug)
        else:
            self._mem = AddressSpace()

        self.proc = m6502(self._mem)
        
        for a in args.breaks:
            try:
                self.proc.add_break(int(a, 16))
            except ValueError:
                print("ERROR: bad format for break %s" % a)
                exit(-1)

        ram = RAM(RAM_SIZE)
        self._mem.add(RAM_ADDR, ram, "SRAM")

        rom = ROM(WOZ_ROM_SIZE, os.path.join(APP_DIR, "wozmon.hex"), WOZ_ROM_ADDR)
        self._mem.add(WOZ_ROM_ADDR, rom, "WROM")
        
    def run(self):
        self.proc.reset()
        self.proc.run()
    

if __name__ == '__main__':

    from application import AppParser
       
    args = AppParser().parse()
    system = Apple1_System(args).run()
    
    

    
