"""
Apple 1 system.

 8 KB RAM           = 0x0000
256 B MON ROM       = 0xff00,  wozmon.hex

"""

from cpu.m6502 import m6502
from dev.io import mc6820
from memory import *

import os
import socket
import threading

from dev.video import VRAM


RAM_ADDR = 0x0000
RAM_SIZE = 0x4000

PIA_ADDR = 0xd010

WOZ_ROM_ADDR = 0xff00
WOZ_ROM_SIZE = 0x0100

APP_DIR = "app_apple1"



class Apple1_Display(object):

    def __init__(self):
        self._sm = VRAM(1, "VMEM_APPLE1")
        self._buf = self._sm._buf
        
    def write(self, value):
        self._buf[0] = value | 0x80
        
    def read(self):
        return self._buf[0]
        
        
class Apple1_Keyboard(object):

    def __init__(self, port, pia, proc):
        self._proc = proc
        self._pia = pia
        self._kb_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._kb_sock.settimeout(2.0)
        self._kb_sock.bind(('', port))
        self._kb_escape = ord('~')
        self._kb_buf = 0x00
        threading.Thread(target = self._kb_recv).start()
        
    def read(self):
        return self._kb_buf
        
    def _kb_recv(self):
        while True:
            try:
                c = int((self._kb_sock.recvfrom(1)[0])[0])
                #print("KB data: %02x" % c)
                if c == self._kb_escape:
                    self._proc.halt()
                    return
                self._kb_buf = c | 0x80
                self._pia.strobe(0)
            except socket.timeout:
                if self._proc.halted():
                    return


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
        
        self._pia = mc6820(self._pia_in, self._pia_out)
        self._mem.add(PIA_ADDR, self._pia, "MPIA")
        
        self._display = Apple1_Display()
        
        self._keyboard = Apple1_Keyboard(50000, self._pia, self.proc)
        
    def _pia_in(self, port):
        if port == 0:
            return self._keyboard.read()
        elif port == 1:
            return self._display.read()
        return 0xff
        
    def _pia_out(self, port, value):
        if port == 1:
            self._display.write(value)
        
    def run(self):
        self.proc.reset()
        self.proc.run()
    

if __name__ == '__main__':

    from application import AppParser
       
    args = AppParser().parse()
    system = Apple1_System(args).run()
    
    

    
