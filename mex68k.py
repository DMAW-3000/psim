"""
Motorola MEX68000 system.

32 KB RAM       = 0x000000
16 KB MON ROM   = 0x080000,   mexmon.hex

App Directory:
app_mex68k

Serial Ports:
1 - primary,     port 50000
2 - secondary,   port 50008

The system boots to the monitor program stored in ROM.
"""

from cpu.mc68000 import mc68000
from memory import *

from dev.serial import mc6850
from dev.timer import mc68230

import os
import threading

RAM_ADDR    = 0x000000
RAM_SIZE    = 0x008000

TROM_ADDR   = 0x008000
TROM_SIZE   = 0x004000

VROM_ADDR   = 0x000000

PTIM_ADDR   = 0x010001
SIO_ADDR    = 0x010040

BROM_ADDR   = 0x020000
BROM_SIZE   = 0x001000

APP_DIR = "app_mex68k"


class MEX_Serial(object):

    def __init__(self, proc):
        self._sio1 = mc6850(50000, proc)
        self._sio2 = mc6850(50008, proc)
        
    def size(self):
        return 4
        
    def write8(self, addr, value):
        if not (addr & 0x1):
            self._sio1.write8(addr >> 1, value)
        else:
            self._sio2.write8(addr >> 1, value)
        
    def read8(self, addr):
        if not (addr & 0x1):
            return self._sio1.read8(addr >> 1)
        else:
            return self._sio2.read8(addr >> 1)
            
            
class MEX_TimerPrinter(object):
    
    def __init__(self, proc, intrCtl, timerIntrLvl, portIntrLvl,
                 portRead, portWrite, statRead, cntlWrite):
        self._pt = mc68230(proc, intrCtl, timerIntrLvl, portIntrLvl, None,
                           portRead, portWrite, statRead, cntlWrite)
        
    def size(self):
        return 63
        
    def write8(self, addr, value):
        self._pt.write8(addr >> 1, value)
        
    def read8(self, addr):
        return self._pt.read8(addr >> 1)
        
    def clk(self):
        self._pt.clk()
        

class MEX_VROM(Memory):

    def __init__(self, rom):
        self._rom = rom
        
    def size(self):
        return 8
        
    def read8(self, addr):
        return self._rom.read8(addr)
        
    def read16be(self, addr):
        return self._rom.read16be(addr)
        
    def write8(self, addr, value):
        pass
        
    def write16be(self, addr, value):
        pass
        

class MEX_Printer(object):

    def __init__(self, outName):
        self._buf = bytearray(1)
        self._ready = True
        self._out_file = open(outName, "wb", 0)
        
    def __del__(self):
        self._out_file.close()
        
    def init(self):
        print("lpt init")
        
    def write_data(self, value):
        self._buf[0] = value
        
    def strobe(self):
        self._ready = False
        threading.Thread(target = self._tx_wait).start()
                    
    def _tx_wait(self):
        self._out_file.write(self._buf)
        self._ready = True
                
    def read_status(self):
        return self._ready
        
        
class MEX_Cassette(object):
    
    def __init__(self, inName, outName):
        self._buf = bytearray(1)
        self._clk_count = None
        self._mask = 0x80
        self._acc = 0x00
        self._bitv = False
        self._bito = None
        self._bit_stop = False
        self._in_file = open(inName, "rb")
        self._out_file = open(outName, "wb", 0)
        
    def clk(self):
        if self._clk_count is not None:
            self._clk_count += 1
        
    def write_bit(self, bit):
        if bit:
            self._clk_count = 0
        else:
            m = self._mask
            if self._clk_count < (50 * 32):
                self._acc |= m
            m >>= 1
            if m == 0x00:
                m = 0x80
                print("cas %02x" % self._acc)
                self._buf[0] = self._acc
                self._acc = 0x00
                threading.Thread(target = self._write_file).start()
            self._mask = m
            self._clk_count = None
            
    def read_bit(self):
        if self._bito is None:
            self._bito = True
            self._bit_stop = False
            self._clk_count = 0
            print("cas start")
            return False
        elif not self._bit_stop:
            if self._bitv:
                if self._clk_count > (31 * 32):
                    self._bito = False
                    self._bit_stop = True
                    print("cas 1")
            else:
                if self._clk_count > (63 * 32):
                    self._bito = False
                    self._bit_stop = True
                    print("cas 0")
        else:
            if self._clk_count > (210 * 32):
                print("cas stop")
                self._read_file()
                self._bito = None
        return self._bito
        
    def _read_file(self):
        m = self._mask
        if m == 0x80:
            data = self._in_file.read(1)
            if len(data):
                self._acc = data[0]
                print("cas %02x" % self._acc)
            else:
                self._count = None
                self._bito = False
                return
        self._bitv = (m & self._acc) != 0x00
        print("cas bit", self._bitv)
        m >>= 1
        if m == 0x00:
            m = 0x80
        self._mask = m
            
    def _write_file(self):
        self._out_file.write(self._buf)
       
       
class MEX_IntrController(object):

    def __init__(self, proc):
        self._proc = proc
        self._level = 0
        self._lock = threading.Lock()
        self._pend = [None] * 8
        self._rng7 = range(7, 0, -1)
        
    def intr(self, level, vector):
        p = self._pend
        if p[level] is not None:
            return
        print("INTR: %d %02x" % (level, vector))
        self._lock.acquire()
        p[level] = vector
        self._level = max(self._level, level)
        self._lock.release()
                
    def intr_level(self):
        return self._level
        
    def intr_ack(self, level):
        p = self._pend
        vec = p[level]
        self._lock.acquire()
        p[level] = None
        self._level = 0
        for n in self._rng7:
            if p[n] is not None:
                self._level = n
                break
        self._lock.release()
        return vec


class MEX_System(object):

    def __init__(self, args):
    
        if args.mem_log:
            self._mem = AddressSpace("mem.txt", not args.debug, True)
        else:
            self._mem = AddressSpace(None, False, True)

        self.proc = mc68000(self._mem, 4, self._clkout,
                            self._intr_level, self._intr_ack)
        
        for a in args.breaks:
            try:
                self.proc.add_break(int(a, 16))
            except ValueError:
                print("ERROR: bad format for break %s" % a)
                exit(-1)

        self._ram = RAM(RAM_SIZE)
        self._mem.add(RAM_ADDR, self._ram, "SRAM")
        
        self._trom = ROM(TROM_SIZE, os.path.join(APP_DIR, "mexmon.hex"), TROM_ADDR)
        self._mem.add(TROM_ADDR, self._trom, "TROM")
        
        self._intr = MEX_IntrController(self.proc)
        
        self._ptim = MEX_TimerPrinter(self.proc, self._intr, 2, 3,
                                      self._lpt_port_read, self._lpt_port_write,
                                      self._lpt_stat_read, self._lpt_cntl_write)
        self._mem.add(PTIM_ADDR, self._ptim, "PTIM")
        
        self._sio = MEX_Serial(self.proc)
        self._mem.add(SIO_ADDR, self._sio, "MSIO")
        
        self._lpt = MEX_Printer(os.path.join(APP_DIR, "lpt0.txt"))
        
        self._cas = MEX_Cassette(os.path.join(APP_DIR, "tapein.cas"),
                                 os.path.join(APP_DIR, "tapeout.cas"))
        
        vrom = MEX_VROM(self._trom)
        self._mem.overlay(VROM_ADDR, vrom, "VROM")
        
        self._brom = ROM(BROM_SIZE, os.path.join(APP_DIR, "tibasic.hex"), 0x8fc)
        self._mem.add(BROM_ADDR, self._brom, "BROM")
        
    def _intr_level(self):
        return self._intr.intr_level()
        
    def _intr_ack(self, level):
        return self._intr.intr_ack(level)
        
    def _lpt_port_write(self, port, value):
        if port == 0:
            self._lpt.write_data(value)
        elif port == 2:
            if value & 0x02:
                self._cas.write_bit(True)
            else:
                self._cas.write_bit(False)
        
    def _lpt_port_read(self, port):
        if port == 1:
            return 0x01
        elif port == 2:
            if self._cas.read_bit():
                return 0x01
        return 0x00
        
    def _lpt_cntl_write(self, value):
        if value & 0x2:
            self._lpt.strobe()
        if value & 0x8:
            self._lpt.init()
        
    def _lpt_stat_read(self):
        val = 0x0
        if self._lpt.read_status():
            val |= 0x1
        return val
        
    def _clkout(self):
        self._ptim.clk()
        self._cas.clk()
        
    def run(self):
        self.proc.run()
    

if __name__ == '__main__':

    from application import AppParser
       
    args = AppParser(False).parse()
    MEX_System(args).run()
    
    

    
