
from threading import Thread, Lock
from pqueue import PQueue

class i8259(object):

    def __init__(self, proc):
        self._proc = proc
        self._icw = 0
        self._ict = 0
        self._mask = 0xff
        self._req = 0x00
        self._isr = 0x00
        self._vec = 0
        self._slave = 0
        self._level= 0xff
        self._rd_reg = 0
        self._stack = []
        self._rng8 = range(8)
        self._q = PQueue(8)
        self._lock = Lock()
        Thread(target = self._service).start()

    def size(self):
        return 2

    def write8(self, addr, value):
        #print("i8259 wr %04x %02x" % (addr, value))
        self._lock.acquire()
        if addr == 0:
            if value & 0x10:      # RESET - ICW1
                print("i8259 reset %02x" % value)
                #if (value & 0x02) != 0x00:
                #    raise RuntimeError("i8259 cascade mode not supported")
                self._mask = 0xff
                self._level = 0xff
                self._req = 0x00
                self._isr = 0x00
                self._rd_reg = 0x00
                self._stack.clear()
                if (value & 0x01) != 0x00:
                    self._icw = 3
                    self._ict = 3
                else:
                    self._icw = 2
                    self._ict = 2
            elif not (value & 0x18):    # OCW2
                if value & 0x04:
                    print("ERROR: i8259 poll cmd not supported")
                    self._proc.halt()
                if value & 0x20:
                    if self._level != 0xff:
                        self._isr &= (~(0x01 << self._level) & 0xff)
                        #print("i8259 EOI %d %02x %02x" % (self._level, self._req, self._isr))
                        self._level = self._stack.pop()
                        self._issue()
                else:
                    print("ERROR: i8259 lost EOI")
                    self._proc.halt()
            elif (value & 0x18) == 0x08:    # OCW3
                if value & 0x02:
                    #print("i8259 rd req")
                    if value & 0x01: 
                        self._rd_reg = self._isr
                    else:
                        self._rd_reg = self._req
        else:
            if self._icw > 0:               # ICW 2-4
                if self._icw == self._ict:
                    self._vec = value & 0xf8
                    #print("i8259 vec %02x" % value)
                elif self._icw == (self._ict - 1):
                    self._slave = value
                    #print("i8259 slave %02x" % value)
                self._icw -= 1
            else:                           # OCW1
                #print("i8259 mask %02x" % value)
                self._mask = value
        self._lock.release()

    def read8(self, addr):
        #print("i8259 rd %04x" % addr)
        if addr == 0:
            return self._rd_reg
        else:
            return self._mask

    def intr(self, level):
        self._lock.acquire()
        self._req |= (0x01 << level)
        self._issue()
        self._lock.release()
        
    def _issue(self):
        m0 = 0x01
        m1 = (~self._mask) & 0xff
        for level in self._rng8:
            if ((m0 & m1 & self._req) != 0x00) and (level < self._level):
                self._req &= (~m0)
                self._isr |= m0
                #print("INTR %d %02x %02x" % (level, self._req, self._isr))
                self._stack.append(self._level)
                self._level = level
                self._q.put(level)
                break
            m0 <<= 1
            
    def _service(self):
        print("i8259 thread started")
        while True:
            level = self._q.get(2.0)
            if level is not None:
                #print("i8259 srv %d" % level)
                self._proc.intr_req(self._vec + level)
            else:
                if self._proc.halted():
                    return
            
            
        
            
