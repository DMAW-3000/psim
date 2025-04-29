"""
Early model IBM PC.

32 KB RAM       = 0x00000
 8 KB BIOS ROM  = 0xfe000,   pcxtbios.hex

App Directory:
app_pcma

Keyboard port 50000.

MDA display with 4KB video RAM.

The system boots BIOS in ROM, which will attempt to load MSDOS from disk A.
"""

from cpu.i8086 import i8086, i8088
from dev.timer import i8253
from dev.dma import i8237
from dev.intrctl import i8259
from dev.fdsk import nec765, FloppyDisk
from dev.serial import ns8250
from dev.video import mc6845, VRAM
from dev.disk import sys_map
from dev.io import i8255
from memory import *

import threading
import os
import socket
import time


RAM_ADDR    = 0x00000
RAM_SIZE    = 0x08000

VRAM_ADDR   = 0xb0000
VRAM_SIZE   = 0x01000

ROM_ADDR    = 0xfe000
ROM_SIZE    = 0x02000

DMA_IO      = 0x0000
INTR_IO     = 0x0020
TIMER_IO    = 0x0040
MB_IO       = 0x0060
PAGE_IO     = 0x0080
NMI_IO      = 0x00a0
LPR_IO      = 0x0378
VIDEO_IO    = 0x03b0
DOR_IO      = 0x03f2
FDC_IO      = 0x03f4
SIO_IO      = 0x03f8

APP_DIR = "app_pcma"


class PCMA_Motherboard(object):

    def __init__(self, proc, ioAs, intrCtl, port):
        self._proc = proc
        self._intr_ctl = intrCtl
        self._pb6 = False
        self._pb7 = False
        self._portb = 0x00
        self._kb_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._kb_sock.settimeout(2.0)
        self._kb_sock.bind(('', port))
        self._kb_escape = 41
        self._kb_buf = 0x00
        self._config0 = 0x05
        self._config1 = 0x07
        self._upper = False
        self._gpio = i8255(self._gpio_read, self._gpio_write)
        ioAs.add(MB_IO, self._gpio, "XSYS")
        threading.Thread(target = self._kb_recv).start()

    def _kb_reset(self):
        print("KB reset")
        self._kb_buf = 0xaa
        self._intr_ctl.intr(1)
        
    def _kb_recv(self):
        while True:
            try:
                c = int((self._kb_sock.recvfrom(1)[0])[0])
                #print("KB data: %02x" % c)
                if c == self._kb_escape:
                    self._proc.halt()
                    return
                while self._kb_buf != 0x00:
                    if self._proc.halted():
                        return
                    time.sleep(0)
                self._kb_buf = c
                self._intr_ctl.intr(1)
            except socket.timeout:
                if self._proc.halted():
                    return
                    
    def _gpio_read(self, port):
        #print("MB:", port)
        if port == 0:
            return self._kb_buf
        elif port == 1:
            return self._portb
        elif port == 2:
            if (self._portb & 0x08) != 0x00:
                return self._config1 & 0x0f
            else:
                return self._config0 & 0x0f
        elif port == 3:
            if (self._portb & 0x08) != 0x00:
                return (self._config1 >> 4) & 0x0f
            else:
                return (self._config0 >> 4) & 0x0f
            
    def _gpio_write(self, port, value):
        #print("MB: %d %02x" % (port, value))
        if port == 1:
            self._portb = value
            if (value & 0x80) != 0x00:
                if not self._pb7:
                    #print("kb clear")
                    self._kb_buf = 0x00
                    self._pb7 = True
            else:
                self._pb7 = False
            if (value & 0x40) != 0x00:
                if not self._pb6:
                    threading.Timer(0.02, self._kb_reset).start()
                    self._pb6 = True
            else:
                self._pb6 = False


class PCMA_PageRegisters(object):

    def __init__(self):
        self.regs = [0x00] * 4

    def size(self):
        return 4

    def write8(self, addr, value):
        #print("DMA page reg wr %d %02x" % (3 - addr, value))
        self.regs[3 - addr] = value

    def read8(self, addr):
        return 0xff


class MDA_Video(object):

    def __init__(self, memAs, ioAs):
        self._vram = VRAM(VRAM_SIZE, "VMEM_MDA")
        memAs.add(VRAM_ADDR, self._vram, "VRAM")
        self._crtc = mc6845()
        ioAs.add(VIDEO_IO + 4, self._crtc, "VCRT")
        ioAs.add(VIDEO_IO + 8, self, "VMDA")
        self._control_reg = 0x00
        self._status_state = 0

    def size(self):
        return 8

    def write8(self, addr, value):
        #print("MDA wr %04x %02x" % (addr, value))
        if addr == 0:
            if not (value & 0x01):
                raise RuntimeError("MDA: low resolution mode not supported")
            self._control_reg = value

    def read8(self, addr):
        #print("MDA rd %04x" % addr)
        if addr == 0:
            return self._control_reg
        elif addr == 2:
            if self._status_state == 0:
                self._status_state = 1
                return 0x09
            else:
                self._status_state = 0
                return 0x00
        return 0x00
        

class PCMA_DigOutReg(object):

    def __init__(self, fdc):
        self._fdc = fdc
        self._r7 = False

    def size(self):
        return 1

    def write8(self, addr, value):
        #print("DOR %02x" % value)
        if value & 0x04:
            if not self._r7:
                self._fdc.reset()
                self._r7 = True
        else:
            self._r7 = False

    def read8(self, addr):
        return 0x00
        
        
class PCMA_NmiMaskReg(object):

    def __init__(self):
        self._reg = 0x00

    def size(self):
        return 1

    def write8(self, addr, value):
        print("NMI MASK %02x" % value)
        self._reg = value

    def read8(self, addr):
        return self._reg
        
        
class PCMA_Printer(object):

    def __init__(self, outName):
        self._data_reg = bytearray(1)
        self._status_reg = 0x80
        self._lock = threading.Lock()
        self._out_file = open(outName, "wb", 0)
        
    def __del__(self):
        self._out_file.close()
        
    def size(self):
        return 4
        
    def write8(self, addr, value):
        #print("lpr reg wr %02x %02x" % (addr, value))
        if addr == 0:
            self._data_reg[0] = value
        elif addr == 2:
            if value & 0x08:
                if not (value & 0x04):
                    print("lpt initialize")
                elif (value & 0x05) == 0x05: 
                    self._lock.acquire()
                    self._status_reg &= 0x7f
                    self._lock.release()
                    threading.Thread(target = self._tx_wait).start()
                
    def _tx_wait(self):
        self._out_file.write(self._data_reg)
        self._lock.acquire()
        self._status_reg |= 0x80
        self._lock.release()
                
    def read8(self, addr):
        #print("lpr reg rd %02x" % addr)
        if addr == 0:
            return self._data_reg[0]
        elif addr == 1:
            return self._status_reg
        else:
            return 0x00
            
            
class PCMA_System(object):

    def __init__(self, args):
    
        self._init_refresh = False
        
        if args.mem_log:
            self._mem = AddressSpace("mem.txt", not args.debug)
        else:
            self._mem = AddressSpace()
        if args.io_log:
            self._io = AddressSpace("io.txt", not args.debug)
        else:
            self._io = AddressSpace()
            
        appDir = "app_pcma"

        self.proc = i8086(self._mem, self._io, 4, self._clkout)
        
        for a in args.breaks:
            try:
                self.proc.add_break(int(a, 16))
            except ValueError:
                print("ERROR: bad format for break %s" % a)
                exit(-1)

        ram = RAM(RAM_SIZE)
        self._mem.add(RAM_ADDR, ram, "LRAM")

        rom = ROM(ROM_SIZE, os.path.join(APP_DIR, "pcxtbios.hex"), 0xe000)
        self._mem.add(ROM_ADDR, rom, "BROM")

        self._video = MDA_Video(self._mem, self._io)

        self._intr = i8259(self.proc)
        self._io.add(INTR_IO, self._intr, "INT0")

        self._mboard = PCMA_Motherboard(self.proc, self._io, self._intr, 50000)

        self._timer = i8253((self._timer0, self._timer1, None))
        self._io.add(TIMER_IO, self._timer, "TIM0")

        fdskChan = i8237.ChannelDesc()
        fdskChan.tcout = self._fdsk_eot
        fdskChan.rdout = self._fdsk_read
        fdskChan.wrout = self._fdsk_write
        self._dma = i8237(self, self.proc, (None, None, fdskChan, None))
        self._io.add(DMA_IO, self._dma, "DMA0")
        
        self._sio = ns8250(50008, self.proc)
        self._io.add(SIO_IO, self._sio, 'SER0')

        self._page_regs = PCMA_PageRegisters()
        self._io.add(PAGE_IO, self._page_regs, "XPAG")

        dsk0 = FloppyDisk(*sys_map["pcxt"], os.path.join(appDir, "fd0.fdd"))
        dsk1 = FloppyDisk(*sys_map["pcxt"], os.path.join(appDir, "fd1.fdd"))
        self._fdc = nec765(self.proc, self._intr, 6, self._dma, 2, 512,
                           dsk0, dsk1, None, None)
        self._io.add(FDC_IO, self._fdc, "FDC0")
        
        self._lpr = PCMA_Printer(os.path.join(APP_DIR, "lpt0.txt"))
        self._io.add(LPR_IO, self._lpr, "LPT0")

        self._dor = PCMA_DigOutReg(self._fdc)
        self._io.add(DOR_IO, self._dor, "XDOR")
        
        self._nmi = PCMA_NmiMaskReg()
        self._io.add(NMI_IO, self._nmi, "XNMI")

    def write8(self, addr, value):
        addr += (self._page_regs.regs[3 - self._dma.cur_chan] << 16)
        #print("dma wr %06x %02x" % (addr, value))
        self._mem.write8(addr, value)

    def read8(self, addr):
        addr += (self._page_regs.regs[3 - self._dma.cur_chan] << 16)
        #print("dma rd %06x" % addr)
        return self._mem.read8(addr)

    def _clkout(self):
        self._timer.clk(0)
        self._timer.clk(1)
        self._timer.clk(2)

    def _timer0(self):
        #print("timer0")
        self._intr.intr(0)

    def _timer1(self):
        #print("timer 1")
        if not self._init_refresh:
            self._dma.req(0)
            self._init_refresh = True
            
    def _fdsk_eot(self):
        self._fdc.eot()
        
    def _fdsk_read(self):
        return self._fdc.data_read()
        
    def _fdsk_write(self, value):
        self._fdc.data_write(value)
        
    def run(self):
        self.proc.reset()
        self.proc.run()
        

if __name__ == '__main__':
    
    from application import AppParser

    args = AppParser().parse()
    system = PCMA_System(args).run()
