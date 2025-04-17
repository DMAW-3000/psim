"""
Intel MDS800 8080 system.

32 KB RAM       = 0x0000
 2 KB MON ROM   = 0xf800,   mon80.hex

App Directory:
app_mds80

Serial Ports:
1 - secondary, port 50000
2 - primary,   port 50008

Paper Tape: tapein.txt, tapeout.txt

The system boots to the MON80 monitor program
stored in ROM.

To boot CPM, from the MON80 prompt:
.R0
.G7B00
"""

from cpu.i8080 import i8080
from memory import *
from dev.serial import i8251
from dev.fdsk import FloppyDisk
from dev.timer import i8253
from dev.disk import sys_map, DiskChanger

from threading import Thread, Lock
from pqueue import PQueue

import os
import socket
import time

RAM_ADDR = 0x0000
RAM_SIZE = 0x8000

FP_ROM_ADDR  = 0x0000
FP_ROM_SIZE  = 0x0100

MON_ROM_ADDR = 0xf800
MON_ROM_SIZE = 0x0800

FLOPPY0_IO  = 0x78
FLOPPY1_IO  = 0x88

TIMER_IO    = 0xe0

SER0_IO     = 0xf4
SER1_IO     = 0xf6
TAPE_IO     = 0xf8

INT_MYST_IO = 0xf3
INT_CNTL_IO = 0xfc

FPAN_IO     = 0xff


class MDS_PaperTape(object):
    """
    MDS800 paper tape reader and writer
    """
    
    def __init__(self, port, proc, readFile, writeFile):
        self._proc = proc
        self._write_file = open(writeFile, 'wt')
        self._read_file = open(readFile, 'rt')
        self._wr_buf = 0x00
        self._rd_buf = 0x00
        self._status_reg = 0x40
        self._lock = Lock()
        self._rd_queue = PQueue(1)
        self._wr_queue = PQueue(1)
        self._changer = DiskChanger(port)
        Thread(target = self._chg_wait).start()
        Thread(target = self._wr_wait).start()
        Thread(target = self._rd_wait).start()
        
    def __del__(self):
        self._write_file.close()
        self._read_file.close()

    def size(self):
        return 2

    def read8(self, addr):
        if addr == 0:
            self._lock.acquire()
            self._status_reg &= 0xfd
            self._lock.release()
            return self._rd_buf
        else:
            return self._status_reg

    def write8(self, addr, value):
        if addr == 0:
            self._wr_buf = value
        else:
            #print("PTP w")
            if value & 0x02:
                self._lock.acquire()
                self._status_reg &= 0xbf
                self._lock.release()
                self._wr_queue.put(0)
                time.sleep(0)
            if value & 0x04:
                self._lock.acquire()
                self._status_reg &= 0xdf
                self._lock.release()
                self._rd_queue.put(0)
                time.sleep(0)

    def _wr_wait(self):
        gf = self._wr_queue.get
        lk = self._lock
        while True:
            c = gf(2.0)
            if c is None:
                if self._proc.halted():
                    return
            else:
                self._write_file.write(chr(self._wr_buf))
                self._write_file.flush()
                lk.acquire()
                self._status_reg |= 0x40
                lk.release()

    def _rd_wait(self):
        gf = self._rd_queue.get
        lk = self._lock
        while True:
            c = gf(2.0)
            if c is None:
                if self._proc.halted():
                    return
            else:
                c = self._read_file.read(1)
                if not len(c):
                    self._rd_buf = 0x00
                else:
                    self._rd_buf = ord(c[0])
                lk.acquire()
                self._status_reg |= 0x20
                lk.release()
        
    def _chg_wait(self):
        while True:
            try:
                cmd = self._changer.recv()
                self._read_file.close()
                print("tape change:", cmd)
                self._read_file = None
                self._read_file = open(cmd, "rt")
                self._read_file.read(1)
                self._read_file.seek(0)
            except socket.timeout:
                if self._proc.halted():
                    return
                    
                    
class MDS_Tty(i8251):

    def write8(self, addr, value):
        if addr == 1:
            value |= 0x05
        i8251.write8(self, addr, value)


class MDS_FloppyController(object):
    """
    MDS800 floppy disk controller device
    """
    
    def __init__(self, memAs, dsk0, dsk1, proc):
        self._write_buf = bytearray(128)
        self._mem = memAs
        self._disk_list = (dsk0, dsk1)
        self._save_lo = 0x00
        self._dstat_reg = 0x00
        self._rtype_reg = 0x00
        self._rbyte_reg = 0x00
        self._proc = proc
        self._queue = PQueue(1)
        Thread(target=self._dma_xfer).start()

    def size(self):
        return 4

    def read8(self, addr):
        #print("FD read: %02x" % addr)
        if addr == 0:
            return self._dstat_reg
        elif addr == 1:
            return self._rtype_reg
        elif addr == 3:
            retval = self._rbyte_reg
            self._rbyte_reg = 0x00
            self._dstat_reg = 0x00
            self._rtype_reg = 0x00
            return retval
        return 0x00
        
    def write8(self, addr, value):
        #print("FD write: %02x %02x" % (addr, value))
        if addr == 1:
            self._save_lo = value
        elif addr == 2:
            self._queue.put((value << 8) + self._save_lo)
            time.sleep(0)            

    def _dma_xfer(self):
        mr = self._mem.read8
        mw = self._mem.write8
        while True:
            caddr = self._queue.get(2.0)
            if caddr is None:
                if self._proc.halted():
                    return
                else:
                    continue
            op = mr(caddr)
            func = mr(caddr + 1)
            nsec = mr(caddr + 2)
            track = mr(caddr + 3)
            sec = mr(caddr + 4) & 0x1f
            maddr = mr(caddr + 5) + (mr(caddr + 6) << 8)
            if ((func & 0x30) == 0x00):
                dsk = self._disk_list[0]
            else:
                dsk = self._disk_list[1]
            if dsk is None:
                self._rtype_reg |= 0x02
                self._rbyte_reg |= 0x01
                self._dstat_reg |= 0x04
                return
            func &= 0x0f
            nbytes = dsk.nbytes()
            if func == 4:
                #print("FD: read sec %02d %02d" % (track, sec))
                buf = dsk.read_sec(track, sec)
                for n in range(nbytes):
                    mw(maddr + n, buf[n])
            elif func == 6:
                #print("FD write sec %02d %02d" % (track, sec))
                buf = self._write_buf
                for n in range(nbytes):
                    buf[n] = mr(maddr + n)
                dsk.write_sec(track, sec, buf)
            else:
                raise RuntimeError("FD: unknown function %d" % func)
            self._rtype_reg = 0x00
            self._dstat_reg |= 0x04


class MDS_InterruptControl(object):
    """
    MDS800 interrupt controller device
    """
    
    def __init__(self, proc):
        self._proc = proc
        self._latch = False
        self._level = 0xff
        self._mask = 0xff
        self._req = 0
        self._rng8 = range(8)
        self._q = PQueue(8)
        self._lock = Lock()
        Thread(target = self._service).start()

    def size(self):
        return 2

    def write8(self, addr, value):
        #print("int wr %02x %02x" % (addr, value))
        self._lock.acquire()
        if addr == 0:
            self._mask = value
        else:
            if value == self._level:
                self._latch = False
                self._level = 0xff
                self._issue()
        self._lock.release()

    def read8(self, addr):
        #print("int cntrl rd %02x" % addr)
        if addr == 0:
            return self._mask
        else:
            return self._level

    def intr(self, level):
        self._lock.acquire()
        self._req |= (0x01 << level)
        #print('INTR %02x %02x %d' % (m, self._mask, self._latch))
        self._issue()
        self._lock.release()
        
    def _issue(self):
        m = 0x01
        mask = (~self._mask) & 0xff
        for level in self._rng8:
            if ((mask & self._req & m) != 0x00) and (not self._latch):
                self._req &= (~m)
                self._latch = True
                self._level = level
                self._q.put(level) 
                break
            m <<= 1
            
    def _service(self):
        gf = self._q.get
        rf = self._proc.intr_req
        while True:
            level = gf(2.0)
            if level is not None:
                rf(0xc7 | (level << 3))
            else:
                if self._proc.halted():
                    return


class MDS_InterruptMystery(object):

    def __init__(self):
        pass

    def size(self):
        return 1

    def write8(self, addr, value):
        #print("int myst wr %02x" % value)
        pass

    def read8(self, addr):
        #print("int myst rd")
        return 0x00
        
        
class MDS_FrontPannel(object):

    def __init__(self, memAs):
        self._mem = memAs
        
    def size(self):
        return 1
        
    def write8(self, addr, value):
        #print("FP disable overlay")
        self._mem.remove()
        
    def read8(self, addr):
        return 0x00
        

class MDS_System(object):

    def __init__(self, args):
    
        if args.mem_log:
            self._mem = AddressSpace("mem.txt", not args.debug)
        else:
            self._mem = AddressSpace()
        if args.io_log:
            self._io = AddressSpace("io.txt", not args.debug)
        else:
            self._io = AddressSpace()

        self.proc = i8080(self._mem, self._io, 10, self._clkout)
        
        for a in args.breaks:
            try:
                self.proc.add_break(int(a, 16))
            except ValueError:
                print("ERROR: bad format for break %s" % a)
                exit(-1)
        
        self._ram = RAM(RAM_SIZE)
        self._mem.add(RAM_ADDR, self._ram, "SRAM")
        
        appDir = "app_mds80"

        self._monTty = MDS_Tty(50000, self.proc)
        self._monCrt = i8251(50008, self.proc)
        self._monTape = MDS_PaperTape(50016, self.proc, 
                                      os.path.join(appDir, "tapein.txt"), 
                                      os.path.join(appDir, "tapeout.txt"))
        self._monRom = ROM(MON_ROM_SIZE, 
                           os.path.join(appDir, "mon80.hex"), 
                           MON_ROM_ADDR)
        self._mem.add(MON_ROM_ADDR, self._monRom, "MROM")
        self._io.add(SER0_IO, self._monTty, "SERT")
        self._io.add(SER1_IO, self._monCrt, "SERC")
        self._io.add(TAPE_IO, self._monTape, "TAPE")

        diskMap = sys_map["mds80"]

        dsk0 = FloppyDisk(*diskMap, os.path.join(appDir, "fd0.fdd"))
        dsk1 = FloppyDisk(*diskMap, os.path.join(appDir, "fd1.fdd"))
        self._fdc0 = MDS_FloppyController(self._mem, dsk0, dsk1, self.proc)
        self._io.add(FLOPPY0_IO, self._fdc0, "FDC0")

        dsk2 = FloppyDisk(*diskMap, os.path.join(appDir, "fd2.fdd"))
        dsk3 = FloppyDisk(*diskMap, os.path.join(appDir, "fd3.fdd"))
        self._fdc1 = MDS_FloppyController(self._mem, dsk2, dsk3, self.proc)
        self._io.add(FLOPPY1_IO, self._fdc1, "FDC1")

        self._int_cntl = MDS_InterruptControl(self.proc)
        self._io.add(INT_CNTL_IO, self._int_cntl, "INTR")

        myst = MDS_InterruptMystery()
        self._io.add(INT_MYST_IO, myst, "MYST")
        
        fpan = MDS_FrontPannel(self._mem)
        self._io.add(FPAN_IO, fpan, "FPAN")
        self._fpRom = ROM(FP_ROM_SIZE, 
                          os.path.join(appDir, "boot80.hex"),
                          FP_ROM_ADDR)
        self._mem.overlay(FP_ROM_ADDR, self._fpRom, "BROM")

        self._timer = i8253((self._timer0, None, None))
        self._io.add(TIMER_IO, self._timer, "TIM0")
        
    def run(self):
        self.proc.reset()
        self.proc.run()

    def _clkout(self):
        self._timer.clk(0)

    def _timer0(self):
        self._int_cntl.intr(6)
    

if __name__ == '__main__':

    from application import AppParser
        
    args = AppParser().parse()
    system = MDS_System(args).run()
    
    

    
