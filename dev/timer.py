

from memory import RAM

from threading import Thread


class i8253(object):

    class _Timer(object):

        def __init__(self, clkout):
            self.clkout = clkout
            self.load = 0xffff
            self.latch = 0x0000
            self.count = 0x0000
            self.mode = 0
            self.rl = 3
            self.msb = False
            self.bbuf = 0

    def __init__(self, clkOut = (None, None, None)):
        self._timers = (self._Timer(clkOut[0]),
                        self._Timer(clkOut[1]),
                        self._Timer(clkOut[2]))

    def size(self):
        return 4

    def write8(self, addr, value):
        #print("8253 wr %d %02x" % (addr, value))
        if addr < 3:
            timer = self._timers[addr]
            if timer.rl == 1:
                timer.load = value
                timer.count = value
                timer.msb = False
            elif timer.rl == 2:
                timer.load = value << 8
                timer.count = timer.load
                timer.msb = True
            else:
                if timer.msb:
                    timer.load |= (value << 8)
                    timer.count = timer.load
                else:
                    timer.load = value
                timer.msb = not timer.msb
        else:
            timer = self._timers[(value >> 6) & 0x03]
            rl = (value >> 4) & 0x03
            if rl == 0:
                timer.latch = timer.count
            else:
                if rl == 2:
                    timer.msb = True
                else:
                    timer.msb = False
                timer.rl = rl
                timer.mode = (value >> 1) & 0x07

    def read8(self, addr):
        if addr < 3:
            timer = self._timers[addr]
            c = timer.latch
            #print("8253 rd %d %04x" % (addr, c))
            if not timer.msb:
                c &= 0xff
            else:
                c >>= 8
            if timer.rl == 3:
                timer.msb = not timer.msb
            return c
        else:
            return 0x00

    def clk(self, i):
        timer = self._timers[i]
        c = timer.count - 1
        if c < 0:
            timer.count = timer.load
        else:
            timer.count = c 
        if c == 0:
            if timer.clkout is not None:
                timer.clkout()
                
                
class m6532(object):

    def __init__(self, ramAddr, ramAddrSpace, ioAddr, ioAddrSpace, clkOut = None):
        ram = RAM(128)
        ramAddrSpace.add(ramAddr, ram, "RRAM")
        ioAddrSpace.add(ioAddr, self, "RIOT")
        self._a = 0x00
        self._b = 0x00
        self._tc = 0x00
        self._mc = 0
        self._mod = 1024
        self._clkout = clkOut

    def size(self):
        return 32

    def read8(self, addr):
        #print("6532 read: %04x" % addr)
        if addr == 0x00:
            return self._a
        elif addr == 0x02:
            return self._b
        elif addr == 0x04:
            #print("clk rd %02x" % self.tc)
            return self._tc
        return 0x00

    def write8(self, addr, value):
        print("6532 write: %04x %02x" % (addr, value))
        if addr == 0x00:
            self._a = value
        elif addr == 0x02:
            self._b = value
        elif addr == 0x14:
            self._mod = 1
            self._mc = 0
            self._tc = value
        elif addr == 0x15:
            self._mod = 8
            self._mc = 0
            self._tc = value
        elif addr == 0x16:
            self._mod = 64
            self._mc = 0
            self._tc = value
        elif addr == 0x17:
            self._mod = 1024
            self._mc = 0
            self._tc = value

    def clk(self):
        mc = self._mc + 1
        if mc == self._mod:
            tc = (self._tc - 1) & 0xff
            if tc == 0x00:
                if self._clkout is not None:
                    self._clkout()
            self._tc = tc
            mc = 0
        self._mc = mc
        
        
class mc68230(object):

    def __init__(self, proc, intrCtl = None, 
                 timerIntrLvl= None, portIntrLvl = None,
                 clkOut = None, portIn = None, portOut = None, 
                 hIn = None, hOut = None):
        self._proc = proc
        self._intr_ctl = intrCtl
        self._timer_intr_level = timerIntrLvl
        self._port_intr_level = portIntrLvl
        self._porta_enable = False
        self._portb_enable = False
        self._port_mode = 0
        self._porta_mode = 0
        self._portb_mode = 0
        self._port_out = portOut
        self._port_in = portIn
        self._h_in = hIn
        self._h_out = hOut
        self._clkout = clkOut
        self._timer_count = 0x000000
        self._scale_count = 0x00
        self._te = False
        
        self._regs = bytearray(32)
        self._regs[0x05] = 0x0f
        self._regs[0x11] = 0x0f
        
        self._keep_write = set((0x1a, 0x05, 0x00, 0x02, 0x03, 0x08, 0x09, 0x0c,
                                0x06, 0x07, 0x10, 0x11, 0x13, 0x14, 0x15))
        
    def size(self):
        return 32
        
    def write8(self, addr, value):
        #print("mc68230 wr %02x %02x" % (addr, value))
        if not (addr in self._keep_write):
            return
        elif addr == 0x1a:
            value = 0x00
        elif addr == 0x05:
            value &= 0xfc
        self._regs[addr] = value
        if addr == 0x00:
            self._porta_enable = (value & 0x10) != 0x00
            self._portb_enable = (value & 0x20) != 0x00
            self._port_mode = (value & 0xc0) >> 6
            if self._port_mode != 0:
                raise RuntimeError("mc68230 port mode %d not supported" % self._port_mode)
        elif addr == 0x02:
            if (value != 0x00) and (value != 0xff):
                raise RuntimeError("mc68230 port A bit mode not supported")
        elif addr == 0x03:
            if (value != 0x00) and (value != 0xff):
                raise RuntimeError("mc68230 port B bit mode not supported")
        elif addr == 0x08:
            if      (self._port_out is not None) and \
                    self._porta_enable and \
                    (self._regs[0x02] == 0xff):
                self._port_out(0, value)
        elif addr == 0x09:
            if      (self._port_out is not None) and \
                    self._portb_enable and \
                    (self._regs[0x03] == 0xff):
                self._port_out(1, value)
        elif addr == 0x0c:
            if self._port_out is not None:
                self._port_out(2, value & self._regs[0x04] & 0x03)
        elif addr == 0x06:
            self._porta_mode = value >> 6
            if self._porta_mode == 3:
                self._porta_mode = 2
            if not (value & 0x20):
                raise RuntimeError("mc68230 H2 input mode not supported")
            self._write_control()
        elif addr == 0x07:
            self._portb_mode = value >> 6
            if self._portb_mode == 3:
                self._portb_mode = 2
            if not (value & 0x20):
                raise RuntimeError("mc68230 H4 input not supported")
            self._write_control()
        elif addr == 0x10:
            if value & 0x01:
                if not self._te:
                    #print("mc68230 timer start")
                    self._timer_count = (self._regs[0x13] << 16) + (self._regs[0x14] << 8) + self._regs[0x15]
                    self._scale_count = 0x1f
                    self._regs[0x1a] = 0x00
                    self._te = True
                else:
                    self._te = False
            else:
                #print("mc68230 timer stop")
                self._te = False
                
    def read8(self, addr):
        #print("mc68230 rd %02x" % addr)
        regs = self._regs
        if addr == 0x08:
            if      (self._port_in is not None) and \
                    self._porta_enable and \
                    (regs[0x02] == 0x00):
                regs[addr] = self._port_in(0)
        elif addr == 0x09:
            if      (self._port_in is not None) and \
                    self._portb_enable and \
                    (regs[0x03] == 0x00):
                regs[addr] = self._port_in(1)
        elif addr == 0x0c:
            if self._port_in is not None:
                regs[addr] = self._port_in(2) & (~regs[0x04]) & 0x03
        elif (addr == 0x0a) or (addr == 0x0b):
            regs[addr] = self._port_in(addr - 0x0a)
        elif addr == 0x0d:
            regs[addr] = self._read_status()
        elif addr == 0x17:
            regs[addr] = self._timer_count >> 16
        elif addr == 0x18:
            regs[addr] = (self._timer_count >> 8) & 0xff
        elif addr == 0x19:
            regs[addr] = self._timer_count & 0xff
        return regs[addr]
        
    def _write_control(self):
        if self._h_out is not None:
            xh = 0x0
            if self._porta_enable:
                hMode = (self._regs[0x06] >> 3) & 0x03
                if hMode == 0x01:
                    xh |= 0x2
            if self._portb_enable:
                hMode = (self._regs[0x07] >> 3) & 0x03
                if hMode == 0x01:
                    xh |= 0x8
            self._h_out(xh)
        
    def _read_status(self):
        if self._h_in is not None:
            xh = self._h_in()
            val = xh << 4
            if not self._porta_enable:
                xh &= 0xe
            if not self._portb_enable:
                xh &= 0xb
            return val | xh
        else:
            return 0x00
            
    def clk(self):
        tc = self._regs[0x10]
        if tc & 0x01:
            if (tc & 0x06) != 0x06:
                self._scale_count = (self._scale_count - 1) & 0x1f
            if self._scale_count != 0x1f:
                return
            c = (self._timer_count - 1) & 0xffffff
            if c == 0x000000:
                print("mc68230 timer exp")
                regs = self._regs
                regs[0x1a] = 0x01
                if tc & 0x10:
                    c = (regs[0x13] << 16) + (regs[0x14] << 8) + regs[0x15]
                imode = tc >> 5
                if (imode == 5) or (imode == 7):
                    self._intr_ctl.intr(self._timer_intr_level, regs[0x11])
                if self._clkout is not None:
                    self._clkout()
            self._timer_count = c

        
                