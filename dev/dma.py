
from threading import Thread, Lock
from pqueue import PQueue

class i8237(object):

    class ChannelDesc(object):
    
        def __init__(self):
            self.tcout = None
            self.rdout = None
            self.wrout = None

    class _DMAChannel(object):

        def __init__(self):
            self.cur_chan = 0
            self.cur_addr = 0x0000
            self.base_addr = 0x0000
            self.cur_count = 0x0000
            self.base_count = 0x0000
            self.msb = False
            self.mode = 3
            self.auto_init = False
            self.forward = True
            self.mask = True
            self.rdout = None
            self.wrout = None
            self.tcout = None

    def __init__(self, memAs, proc, fOut = (None, None, None, None)):
        self._enabled = False
        self._mem = memAs
        self._proc = proc
        self._msb = False
        self._status_reg = 0x00
        self._temp_reg = 0x00
        self._q = PQueue(4)
        self._lock = Lock()
        self._channels = (self._DMAChannel(), self._DMAChannel(),
                          self._DMAChannel(), self._DMAChannel())
        for n in range(4):
            if fOut[n] is not None:
                chan = self._channels[n]
                chan.rdout = fOut[n].rdout
                chan.wrout = fOut[n].wrout
                chan.tcout = fOut[n].tcout
        Thread(target = self._dma_xfer).start()

    def size(self):
        return 16

    def _dma_xfer(self):
        print("i8237 thread started")
        while True:
            ci = self._q.get(2.0)
            if ci is None:
                if self._proc.halted():
                    return
            else:
                self.cur_chan = ci
                chan = self._channels[ci]
                mem = self._mem
                #print("DMA req %d %d %04x %d" % (ci, chan.mode, chan.base_addr, chan.base_count))
                for n in range(chan.base_count + 1):
                    addr = chan.cur_addr
                    if chan.mode == 2:
                        self._temp_reg = mem.read8(addr)
                        if chan.wrout is not None:
                            chan.wrout(self._temp_reg)
                    elif chan.mode == 1:
                        if chan.rdout is not None:
                            self._temp_reg = chan.rdout()
                        mem.write8(addr, self._temp_reg)
                    if chan.forward:
                        chan.cur_addr = (addr + 1) & 0xffff
                    else:
                        chan.cur_addr = (addr - 1) & 0xffff
                    chan.cur_count = (chan.cur_count - 1) & 0xffff
                self._lock.acquire()
                self._status_reg &= ~(0x01 << (ci + 4))
                self._status_reg |= (0x01 << ci)
                self._lock.release()
                if chan.auto_init:
                    chan.cur_count = chan.base_count
                    chan.cur_addr = chan.base_addr
                if chan.tcout is not None:  
                    chan.tcout()


    def req(self, chanIndex):
        chan = self._channels[chanIndex]
        if self._enabled and (not chan.mask):
            if self._q.full():
                print("i8237 QUEUE OVERFLOW!!!")
                self._proc.halt()
                return
            self._lock.acquire()
            self._status_reg |= (0x01 << (chanIndex + 4))
            self._lock.release()
            self._q.put(chanIndex)

    def write8(self, addr, value):
        #print("i8237 wr %04x %02x" % (addr, value))
        if (addr == 0) or (addr == 2) or (addr == 4) or (addr == 6):
            chan = self._channels[addr >> 1]
            if self._msb:
                chan.cur_addr = (value << 8) | self._wr_buf
                chan.base_addr = chan.cur_addr
                self._msb = False
            else:
                self._wr_buf = value
                self._msb = True
        elif (addr == 1) or (addr == 3) or (addr == 5) or (addr == 7):
            chan = self._channels[addr >> 1]
            if self._msb:
                chan.cur_count = (value << 8) | self._wr_buf
                chan.base_count = chan.cur_count
                self._msb = False
            else:
                self._wr_buf = value
                self._msb = True
        elif addr == 8:
            if value & 0x01:
                raise RuntimeError("i8237 mem-to-mem not supported")
            self._enabled = (value & 0x04) == 0x00
        elif addr == 10:
            ci = value & 0x03
            chan = self._channels[ci]
            chan.mask = (value & 0x04) != 0x00
        elif addr == 11:
            ci = value & 0x03
            chan = self._channels[ci]
            chan.mode = (value >> 2) & 0x03
            chan.auto_init = (value & 0x10) != 0x00
            chan.forward = (value & 0x20) == 0x00
            #print("i8237 mode chan=%d %d" % (ci, chan.mode))
        elif addr == 12:
            self._msb = False
        elif addr == 13:
            print("i8237 reset")
            self._enabled = False
            self._msb = False
            self._lock.acquire()
            self._status_reg = 0x00
            self._lock.release()
            for chan in self._channels:
                self.mask = True
        elif addr == 14:
            for chan in self._channels:
                chan.mask = False
        elif addr == 15:
            for chan in self._channels:
                chan.mask = True
        else:
            print("i8237 unknown wr addr %d" % addr)

    def read8(self, addr):
        #print("i8237 rd %04x" % addr)
        if (addr == 0) or (addr == 2) or (addr == 4) or (addr == 6):
            chan = self._channels[addr >> 1]
            if self._msb:
                self._msb = False
                return self._rd_buf >> 8
            else:
                self._msb = True
                self._rd_buf = chan.cur_addr
                return self._rd_buf & 0xff
        elif (addr == 1) or (addr == 3) or (addr == 5) or (addr == 7):
            chan = self._channels[addr >> 1]
            if self._msb:
                self._msb = False
                return self._rd_buf >> 8
            else:
                self._msb = True
                self._rd_buf = chan.cur_count
                return self._rd_buf & 0xff
        elif addr == 8:
            self._lock.acquire()
            rv = self._status_reg
            self._status_reg &= 0xf0
            self._lock.release()
            return rv
        elif addr == 13:
            return self._temp_reg
        print("i8237 unknown rd addr %d" % addr)
        return 0x00