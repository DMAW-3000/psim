
from cpu.i8086 import i8086

class i286(i8086):

    class ExtendedFlags(object):
        
        def __init__(self):
            self.nt = False
            self.iopl = 0
            
    class SegmentDescriptor(object):
    
        def __init__(self):
            self.p      = False
            self.dpl    = 0
            self.type   = 0
            self.a      = 0
            self.base   = 0x000000
            self.limit  = 0x0000
            

    def __init__(self, memAs, ioAs, mips = 1.0, clkOut = None):
    
        self._ext_flags = self.ExtendedFlags()
        
        self._msw           = 0x0000
        self._gdtr_base     = 0x000000
        self._gdtr_limit    = 0x0000
        self._ldtr_base     = 0x000000
        self._ldtr_limit    = 0x0000
        self._idtr_base     = 0x000000
        self._idtr_limit    = 0x0000
        
        self._n_desc = "_desc"
        
        self._cs_sel = 0x0000
        self._ss_sel = 0x0000
        self._ds_sel = 0x0000
        self._es_sel = 0x0000
        
        self._cs_desc = self.SegmentDescriptor()
        self._ds_desc = self.SegmentDescriptor()
        self._ss_desc = self.SegmentDescriptor()
        self._es_desc = self.SegmentDescriptor()
        
        i8086.__init__(self, memAs, ioAs, mips, clkOut)
        
    def _get_flags(self):
        t = i8086._get_flags(self)
        f = self._ext_flags
        if f.nt:
            t |= 0x4000
        t |= (f.iopl << 12)
        return t

    def _put_flags(self, value):
        i8086._put_flags(self, value)
        f = self._ext_flags
        f.nt = (value & 0x4000) != 0x0000
        f.iopl = (value & 0x3000) >> 12
        
    @property
    def _cs(self):
        return self._cs_sel

    @_cs.setter
    def _cs(self, value):
        if self._msw & 0x0001:
            if value != self._cs_sel:
                addr = value & 0xfff8
                if value & 0x0004:
                    addr += self._ldtr_base
                else:
                    addr += self._gdtr_base
                self._load_desc(self._cs_desc, addr)
                self._cs_sel = value
        else:
            self._cs_sel = value
            
    @property
    def _ds(self):
        return self._ds_sel

    @_ds.setter
    def _ds(self, value):
        if self._msw & 0x0001:
            if value != self._ds_sel:
                addr = value & 0xfff8
                if value & 0x0004:
                    addr += self._ldtr_base
                else:
                    addr += self._gdtr_base
                self._load_desc(self._ds_desc, addr)
                self._ds_sel = value
        else:
            self._ds_sel = value
            
    @property
    def _ss(self):
        return self._ss_sel

    @_ss.setter
    def _ss(self, value):
        if self._msw & 0x0001:
            if value != self._ss_sel:
                addr = value & 0xfff8
                if value & 0x0004:
                    addr += self._ldtr_base
                else:
                    addr += self._gdtr_base
                self._load_desc(self._ss_desc, addr)
                self._ss_sel = value
        else:
            self._ss_sel = value
            
    @property
    def _es(self):
        return self._es_sel

    @_ds.setter
    def _es(self, value):
        if self._msw & 0x0001:
            if value != self._es_sel:
                addr = value & 0xfff8
                if value & 0x0004:
                    addr += self._ldtr_base
                else:
                    addr += self._gdtr_base
                self._load_desc(self._es_desc, addr)
                self._es_sel = value
        else:
            self._es_sel = value
            
    def _load_desc(self, desc, addr):
        mr = self._mem.read16le
        basetype = mr(addr + 4)
        desc.p = (basetype & 0x8000) != 0x0000
        desc.a = (basetype & 0x0100) != 0x0000
        desc.type = (basetype & 0x0e00) >> 9
        desc.dpl = (basetype & 0x7000) >> 12
        desc.base = mr(addr + 2) + ((basetype & 0x00ff) << 16)
        desc.limit = mr(addr)
            
    def _data_read8(self, seg, offset):
        if self._msw & 0x0001:
            desc = getattr(self, seg + self._n_desc)
            if offset > desc.limit:
                print("ERROR: offset overflow %04x %04x" % (offset, desc.limit))
                self.halt()
                return 0
            return self._mem.read8(desc.base + offset)
        else:
            return i8086._data_read8(self, seg, offset)
            
    def _data_write8(self, seg, offset, value):
        if self._msw & 0x0001:
            desc = getattr(self, seg + self._n_desc)
            if offset > desc.limit:
                print("ERROR: offset overflow %04x %04x" % (offset, desc.limit))
                self.halt()
                return
            return self._mem.write8(desc.base + offset, value)
        else:
            return i8086._data_write8(self, seg, offset, value)
            
            
    def _print_state(self):
        i8086._print_state(self)
        print("MSW=%04x" % self._msw)
        if (self._msw & 0x0001) != 0x0000:
            print("GDTR=%08x %04x" % (self._gdtr_base, self._gdtr_limit))
            print("LDTR=%08x %04x" % (self._ldtr_base, self._ldtr_limir))
            print("CD=%08x %04x" % (self._cs_desc.base, self._cs_desc.limit))
            print("SD=%08x %04x" % (self._ss_desc.base, self._ss_desc.limit))
            print("DD=%08x %04x" % (self._ds_desc.base, self._ds_desc.limit))
            print("ED=%08x %04x" % (self._es_desc.base, self._es_desc.limit))
            print()