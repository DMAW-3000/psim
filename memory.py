"""
Bus and memory emulation
"""

class BusError(RuntimeError): 
    """
    Raised to signal a bus error
    """
    pass


class AddressSpace(object): 
    """
    Represents a bus address space
    """

    def __init__(self, trc = None, trcEnable = False, busError = False):
        """
        Create a new address space
        """
        self._mlist = []
        self._bus_error = busError
        self._err_info = None
        self._err_addr = None
        if trc is not None:
            self._trc = open(trc, "wt")
        else:
            self._trc = None
        self._trc_enable = trcEnable
        
    def enable_trc(self):
        """
        Enable bus tracing
        """
        self._trc_enable = True
        
    def disable_trc(self):
        """
        Disable bus tracing
        """
        self._trc_enable = False

    def add(self, startAddr, memObj, name):
        """
        Add a new component to the address space
        """
        self._mlist.append((startAddr, startAddr + memObj.size(), memObj, name))

    def overlay(self, startAddr, memObj, name):
        """
        Add a new component to the head of the address space list
        """
        self._mlist.insert(0, (startAddr, startAddr + memObj.size(), memObj, name))

    def remove(self):
        """
        Remove the first component in the address space list
        """
        self._mlist.pop(0)
        
    def get_error(self):
        return (self._err_info, self._err_addr)
    
    def read8(self, address):
        """
        Read one 8-bit byte
        """
        value = 0xff
        tgt = None
        for r in self._mlist:
            if (address >= r[0]) and (address < r[1]):
                value = r[2].read8(address - r[0])
                tgt = r
                break
        if self._bus_error and (tgt is None):
            self._err_info = 1
            self._err_addr = address
            raise BusError
        if (self._trc is not None) and self._trc_enable:
            if tgt is None:
                name = '????'
            else:
                name = tgt[3]
            self._trc.write("%08x R %4s %02x\n" % (address, name, value))
            self._trc.flush()
        return value

    def write8(self, address, value):
        """
        Write one 8-bit byte
        """
        tgt = None
        for r in self._mlist:
            if (address >= r[0]) and (address < r[1]):
                r[2].write8(address - r[0], value)
                tgt = r
                break
        if self._bus_error and (tgt is None):
            self._err_info = 0
            self._err_addr = address
            raise BusError
        if (self._trc is not None) and self._trc_enable:
            if tgt is None:
                name = '????'
            else:
                name = tgt[3]
            self._trc.write("%08x W %4s %02x\n" % (address, name, value))
            self._trc.flush()

    def read16le(self, address):
        """
        Read a 16-bit word using little-ending byte ordering
        """
        value = 0xffff
        tgt = None
        for r in self._mlist:
            if (address >= r[0]) and (address < r[1]):
                value = r[2].read16le(address - r[0])
                tgt = r
                break
        if self._bus_error and (tgt is None):
            self._err_info = 1
            self._err_addr = address
            raise BusError
        if (self._trc is not None) and self._trc_enable:
            if tgt is None:
                name = '????'
            else:
                name = tgt[3]
            self._trc.write("%08x R %4s %04x\n" % (address, name, value))
            self._trc.flush()
        return value

    def write16le(self, address, value):
        """
        Write a 16-bit word using little-ending byte ordering
        """
        tgt = None
        for r in self._mlist:
            if (address >= r[0]) and (address < r[1]):
                r[2].write16le(address - r[0], value)
                tgt = r
                break
        if self._bus_error and (tgt is None):
            self._err_info = 0
            self._err_addr = address
            raise BusError
        if (self._trc is not None) and self._trc_enable:
            if tgt is None:
                name = '????'
            else:
                name = tgt[3]
            self._trc.write("%08x W %4s %04x\n" % (address, name, value))
            self._trc.flush()
            
    def read16be(self, address):
        """
        Read a 16-bit word using big-ending byte ordering
        """
        value = 0xffff
        tgt = None
        for r in self._mlist:
            if (address >= r[0]) and (address < r[1]):
                value = r[2].read16be(address - r[0])
                tgt = r
                break
        if self._bus_error and (tgt is None):
            self._err_info = 1
            self._err_addr = address
            raise BusError
        if (self._trc is not None) and self._trc_enable:
            if tgt is None:
                name = '????'
            else:
                name = tgt[3]
            self._trc.write("%08x R %4s %04x\n" % (address, name, value))
            self._trc.flush()
        return value

    def write16be(self, address, value):
        """
        Write a 16-bit word using big-ending byte ordering
        """
        tgt = None
        for r in self._mlist:
            if (address >= r[0]) and (address < r[1]):
                r[2].write16be(address - r[0], value)
                tgt = r
                break
        if self._bus_error and (tgt is None):
            self._err_info = 0
            self._err_addr = address
            raise BusError
        if (self._trc is not None) and self._trc_enable:
            if tgt is None:
                name = '????'
            else:
                name = tgt[3]
            self._trc.write("%08x W %4s %04x\n" % (address, name, value))
            self._trc.flush()


class Memory(object):
    """
    Generic memory
    """

    def __init__(self, size):
        """
        Create memory of size bytes
        """
        self._m = bytearray(size)

    def size(self):
        """
        Returns size of memory in bytes
        """
        return len(self._m)

    def read8(self, address):
        """
        Read one 8-bit byte
        """
        return self._m[address]

    def write8(self, address, value):
        """
        Write one 8-bit byte
        """
        self._m[address] = value

    def read16le(self, address):
        """
        Read a 16-bit word using little-ending byte ordering
        """
        m = self._m
        return (m[address + 1] << 8) + m[address]

    def write16le(self, address, value):
        """
        Write a 16-bit word using little-ending byte ordering
        """
        m = self._m
        m[address] = value & 0xff
        m[address + 1] = value >> 8
        
    def read16be(self, address):
        """
        Read a 16-bit word using big-ending byte ordering
        """
        m = self._m
        return (m[address] << 8) + m[address + 1]

    def write16be(self, address, value):
        """
        Read a 16-bit word using big-ending byte ordering
        """
        m = self._m
        m[address] = value >> 8
        m[address + 1] = value & 0xff
        

class RAM(Memory): 
    """
    Generic RAM memory
    """
    pass


class ROM(Memory):
    """
    ROM memory loadable with a hex file
    """
    
    def __init__(self, size, hexFile, addr, autoLoad = True):
        Memory.__init__(self, size)
        self._addr = addr
        if autoLoad:
            self._load(hexFile)

    def write8(self, address, value):
        """
        Write operations do nothing
        """
        pass

    def write16le(self, address, value):
        """
        Write operations do nothing
        """
        pass
        
    def write16be(self, address, value):
        """
        Write operations do nothing
        """
        pass

    def _load(self, hexFile):
        """
        Load a hex file into ROM
        """
        f = open(hexFile, 'rt')
        self._loadSREC(f)
        f.close()
        
    def _loadSREC(self, f):
        """
        Load Motorolla SREC hex file
        """
        for line in f:
            if line.startswith('S1'):
                n = int(line[2:4], 16) - 3
                offset = int(line[4:8], 16) - self._addr
                for i in range(n):
                    self._m[offset+i] = int(line[8+(i*2):10+(i*2)], 16)
