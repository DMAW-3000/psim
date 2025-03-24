

from threading import Thread
import time

from dev.disk import Disk


def create_disk(nhead, ntrack, nsector, nbytes, datFile):
    dsk = FloppyDisk(nhead, ntrack, nsector, nbytes, datFile)
    dsk.create()
  
class FloppyDisk(Disk): pass


class nec765(object):

    class CmdDesc(object):
    
        def __init__(self, cmdCount, cmdFunc):
            self.cmd_count = cmdCount
            self.cmd_func = cmdFunc
            
    class Drive(object):
        
        def __init__(self, drvNum, disk):
            self.disk = disk
            self.drv_num = drvNum
            self.cur_head = 0
            self.cur_track = 0
            self.cur_sec = 1

    def __init__(self, proc, intrCtl, intrLevel, dmaCtl, dmaChan, secSize,
                 dsk0, dsk1, dsk2, dsk3):
        self._proc = proc
        self._intr_ctl = intrCtl
        self._intr_level = intrLevel
        self._dma_ctl = dmaCtl
        self._dma_chan = dmaChan
        self._eot_flag = False
        self._msr = 0x00
        self._cmd_regs = [0x00] * 9
        self._status_regs = [0x00] * 7
        self._cur_cmd = None
        self._scount = 0
        self._scur = 0
        self._ccount = 0
        self._ccur = 0
        self._write_buf = bytearray(secSize)
        self._read_buf = None
        self._data_idx = 0
        self._sec_size = secSize
        self._cur_drv = None
        self._drv_list = (self.Drive(0, dsk0), self.Drive(1, dsk1), 
                          self.Drive(2, dsk2), self.Drive(3, dsk3))
        
        readCmd = self.CmdDesc(9, self._read)
        writeCmd = self.CmdDesc(9, self._write)
        
        self._cmd_map = {
            0x08 : self.CmdDesc(1, self._intr_status),
            0x03 : self.CmdDesc(3, self._specify),
            0x07 : self.CmdDesc(2, self._recalibrate),
            0x0f : self.CmdDesc(3, self._seek),
            
            0x06 : readCmd, 
            0x26 : readCmd, 
            0x46 : readCmd, 
            0x66 : readCmd,
            0x86 : readCmd,
            0xa6 : readCmd,
            0xc6 : readCmd,
            0xe6 : readCmd,
            
            0x05 : writeCmd,
            0x25 : writeCmd,
            0x45 : writeCmd,
            0x65 : writeCmd,
            0x85 : writeCmd,
            0xa5 : writeCmd,
            0xc5 : writeCmd,
            0xe5 : writeCmd,
        }

    def size(self):
        return 2

    def reset(self):
        Thread(target = self._do_reset).start()

    def _do_reset(self):
        print("nec765 reset")
        self._msr = 0x80
        self._status_regs[0] = 0xc0
        self._status_regs[1] = 0
        self._intr_ctl.intr(self._intr_level)
        
    def data_read(self):
        i = self._data_idx
        if i == self._sec_size:
            drv = self._cur_drv
            sector = drv.cur_sec + 1
            self._read_buf = drv.disk.read_sec(drv.cur_track, sector, drv.cur_head)
            drv.cur_sec = sector
            i = 0
        value = self._read_buf[i]
        self._data_idx = i + 1    
        return value
        
    def data_write(self, value):
        i = self._data_idx
        self._write_buf[i] = value
        i += 1
        if i == self._sec_size:
            drv = self._cur_drv
            sector = drv.cur_sec
            drv.disk.write_sec(drv.cur_track, sector, self._write_buf, drv.cur_head)
            drv.cur_sec = sector + 1
            i = 0
        self._data_idx = i
        
    def eot(self):
        self._eot_flag = True
        #print("nec765 DMA EOT")

    def write8(self, addr, value):
        #print("nec765 wr %d %02x" % (addr, value))
        if addr == 1:
            if self._cur_cmd is None:
                try:
                    self._cur_cmd = self._cmd_map[value & 0x1f]
                except KeyError:
                    raise RuntimeError("nec765 unknown cmd %02x" % value)
                self._ccount = self._cur_cmd.cmd_count
                self._msr |= 0x10
                #print("nec765 new cmd %02x %d" % (value, self._ccount))
            self._cmd_regs[self._ccur] = value
            self._ccur += 1
            if self._ccur == self._ccount:
                self._msr &= 0x2f
                Thread(target = self._cur_cmd.cmd_func).start()
                self._cur_cmd = None
                self._ccount = 0
                self._ccur = 0

    def read8(self, addr):
        if addr == 0:
            #print("nec765 msr %02x" % self._msr)
            return self._msr
        else:
            rv = self._status_regs[self._scur]
            #print("nec765 sread %d %02x" % (self._scur, rv))
            self._scur += 1
            if self._scur == self._scount:
                #print("nec765 sread done")
                self._msr &= 0xaf
                self._scount= 0
                self._scur = 0
            return rv
        
    def _intr_status(self):
        #print("nec765 cmd int sense")
        self._scount = 2
        self._msr |= 0xd0
        
    def _specify(self):
        #print("nec765 cmd specify")
        if (self._cmd_regs[2] & 0x01) != 0:
            raise RuntimeError("nec765 specify requires DMA mode")
        self._scount = 0
        self._msr |= 0x80
        
    def _recalibrate(self):
        drv = self._drv_list[self._cmd_regs[1] & 0x03]
        drv.cur_head = 0
        drv.cur_track = 0
        drv.cur_sec = 1
        #print("nec765 cmd recal %d" % drv.drv_num)
        self._scount = 0
        self._status_regs[0] = (drv.drv_num | (drv.cur_head << 2))
        self._status_regs[1] = 0x00
        self._msr |= 0x80
        self._intr_ctl.intr(self._intr_level)
        
    def _seek(self):
        drv = self._drv_list[self._cmd_regs[1] & 0x03]
        track = self._cmd_regs[2]
        self._scount = 0
        if track >= drv.disk.ntrack():
            print("nec765 seek error %d %d %d" % (drv.drv_num, track, drv.disk.ntrack()))
            self._status_regs[0] = (0x80 | drv.drv_num | (drv.cur_head << 2))
            self._status_regs[1] = 0x00
            self._intr_ctl.intr(self._intr_level)
            return
        #print("nec765 cmd seek %d %d" % (drv.drv_num, track))
        drv.cur_track = track
        self._status_regs[0] = (0x20 | drv.drv_num | (drv.cur_head << 2))
        self._status_regs[1] = 0x00
        self._msr |= 0x80
        self._intr_ctl.intr(self._intr_level)
        
    def _read(self):
        cregs = self._cmd_regs
        sregs = self._status_regs
        drv = self._drv_list[cregs[1] & 0x03]
        disk = drv.disk
        track = cregs[2]
        head = cregs[3]
        sector = cregs[4]
        nbytes = (cregs[5] * 256)
        self._scount = 7
        #print("nec765 cmd read %d %d %d %d" % (drv.drv_num, track, sector, nbytes))
        if      (track != drv.cur_track) or \
                (head >= disk.nhead()) or \
                (track >= disk.ntrack()) or \
                (sector < 1) or \
                (sector > disk.nsector()) or \
                (nbytes != self._sec_size):
            print("nec765 read error")
            sregs[0] = (0x80 | drv.drv_num | (head << 2))
            sregs[1] = 0x00
            if sector > disk.nsector():
                sregs[1] |= 0x80
            sregs[2] = 0x00
            if track != drv.cur_track:
                sregs[2] |= 0x10
            sregs[3:7] = cregs[2:6]
            self._msr |= 0xd0
            self._intr_ctl.intr(self._intr_level)
            self._read_buf = None
            return
        self._cur_drv = drv
        drv.cur_head = head
        drv.cur_sec = sector
        self._read_buf = disk.read_sec(track, sector, head)
        self._wait_dma()
        sregs[0] = (drv.drv_num | (head << 2))
        sregs[1] = 0x00
        sregs[2] = 0x00
        sregs[3] = track
        sregs[4] = head
        sregs[5] = drv.cur_sec
        sregs[6] = cregs[5]
        self._msr |= 0xd0
        self._intr_ctl.intr(self._intr_level)
        self._read_buf = None
        
    def _write(self):
        cregs = self._cmd_regs
        sregs = self._status_regs
        drv = self._drv_list[cregs[1] & 0x03]
        disk = drv.disk
        track = cregs[2]
        head = cregs[3]
        sector = cregs[4]
        nbytes = (cregs[5] * 256)
        self._scount = 7
        #print("nec765 cmd write %d %d %d %d" % (drv.drv_num, track, sector, nbytes))
        if      (track != drv.cur_track) or \
                (head >= disk.nhead()) or \
                (track >= disk.ntrack()) or \
                (sector < 1) or \
                (sector > disk.nsector()) or \
                (nbytes != self._sec_size):
            print("nec765 write error")
            sregs[0] = (0x80 | drv.drv_num | (head << 2))
            sregs[1] = 0x00
            if sector > disk.nsector():
                sregs[1] |= 0x80
            sregs[2] = 0x00
            if track != drv.cur_track:
                sregs[2] |= 0x10
            sregs[3:7] = cregs[2:6]
            self._msr |= 0xd0
            self._intr_ctl.intr(self._intr_level)
            self._read_buf = None
            return
        self._cur_drv = drv
        drv.cur_head = head
        drv.cur_sec = sector
        self._wait_dma()
        sregs[0] = (drv.drv_num | (head << 2))
        sregs[1] = 0x00
        sregs[2] = 0x00
        sregs[3] = track
        sregs[4] = head
        sregs[5] = drv.cur_sec
        sregs[6] = cregs[5]
        self._msr |= 0xd0
        self._intr_ctl.intr(self._intr_level)
        self._read_buf = None
        
    def _wait_dma(self):
        self._data_idx = 0
        self._eot_flag = False
        self._dma_ctl.req(self._dma_chan)
        while not self._eot_flag:
            if self._proc.halted():
                return
            time.sleep(0)
        