
from processor import Processor

import collections


class i8086(Processor):

    class _Flags(object):

        def __init__(self):
            self.o = False
            self.d = False
            self.i = False
            self.s = False
            self.z = False
            self.a = False
            self.p = False
            self.c = False
            
            
    def __init__(self, memAs, ioAs, mips = 1.0, clkOut = None):
        Processor.__init__(self, mips, clkOut)
        
        self._flags = self._Flags()
        self._iq = collections.deque(maxlen = 6)
        
        self._rng16 = range(16)
        self._rng8 = range(8)
        
        self._mem = memAs
        self._io = ioAs
        
        self._ptr_offset_cache = None
        self._ptr_pci_cache = None
        
        self._ord_seg = None
        self._ord_clear = False
        
        self._rep_op = None
        self._rep_zero = False
        self._rep_start = False
        self._rep_chk = False
        
        self._ip = 0x0000
        self._pf = 0x0000
        self._ax = 0x0000
        self._bx = 0x0000
        self._cx = 0x0000
        self._dx = 0x0000
        self._bp = 0x0000
        self._si = 0x0000
        self._di = 0x0000
        self._sp = 0x0000
        
        self._cs = 0x0000
        self._ds = 0x0000
        self._es = 0x0000
        self._ss = 0x0000

        self._reg_map16 = ("_ax", "_cx", "_dx", "_bx",
                           "_sp", "_bp", "_si", "_di")

        self._reg_map8 = ("_al", "_cl", "_dl", "_bl",
                          "_ah", "_ch", "_dh", "_bh")

        self._seg_map = ("_es", "_cs", "_ss", "_ds")
        
        m = self._seg_map
        self._n_es = m[0]
        self._n_cs = m[1]
        self._n_ss = m[2]
        self._n_ds = m[3]

        self._op_map = [None] * 256
        m = self._op_map
        
        m[0x90] = self._nop
        m[0xf4] = self._hlt

        m[0x88] = self._movregrd8
        m[0x89] = self._movregrd16
        m[0x8a] = self._movregwr8
        m[0x8b] = self._movregwr16

        m[0xc7] = self._movi16
        m[0xc6] = self._movi8

        m[0x8c] = self._movsegrd
        m[0x8e] = self._movsegwr

        m[0xa1] = self._movaxwr
        m[0xa3] = self._movaxrd
        m[0xa0] = self._movalwr
        m[0xa2] = self._movalrd

        m[0xb0] = self._movial
        m[0xb1] = self._movicl
        m[0xb2] = self._movidl
        m[0xb3] = self._movibl
        m[0xb4] = self._moviah
        m[0xb5] = self._movich
        m[0xb6] = self._movidh
        m[0xb7] = self._movibh

        m[0xb8] = self._moviax
        m[0xb9] = self._movicx
        m[0xba] = self._movidx
        m[0xbb] = self._movibx
        m[0xbc] = self._movisp
        m[0xbd] = self._movibp
        m[0xbe] = self._movisi
        m[0xbf] = self._movidi

        m[0xe4] = self._in8
        m[0xe6] = self._out8
        m[0xec] = self._invar8
        m[0xee] = self._outvar8

        m[0xa5] = self._movs16
        m[0xa4] = self._movs8
        m[0xab] = self._stos16
        m[0xaa] = self._stos8
        m[0xad] = self._lods16
        m[0xac] = self._lods8
        m[0xa7] = self._cmps16
        m[0xa6] = self._cmps8
        m[0xaf] = self._scas16
        m[0xae] = self._scas8

        m[0x50] = self._pushax
        m[0x51] = self._pushcx
        m[0x52] = self._pushdx
        m[0x53] = self._pushbx
        m[0x55] = self._pushbp
        m[0x56] = self._pushsi
        m[0x57] = self._pushdi

        m[0x06] = self._pushes
        m[0x0e] = self._pushcs
        m[0x16] = self._pushss
        m[0x1e] = self._pushds

        m[0x8f] = self._poprm

        m[0x58] = self._popax
        m[0x59] = self._popcx
        m[0x5a] = self._popdx
        m[0x5b] = self._popbx
        m[0x5d] = self._popbp
        m[0x5e] = self._popsi
        m[0x5f] = self._popdi

        m[0x07] = self._popes
        m[0x17] = self._popss
        m[0x1f] = self._popds

        m[0x9c] = self._pushf
        m[0x9d] = self._popf

        m[0xc4] = self._les
        m[0xc5] = self._lds
        m[0x8d] = self._lea
        m[0xd7] = self._xlat

        m[0x87] = self._xchg16
        m[0x86] = self._xchg8
        m[0x90] = self._xchga
        m[0x91] = self._xchga
        m[0x92] = self._xchga
        m[0x93] = self._xchga
        m[0x94] = self._xchga
        m[0x95] = self._xchga
        m[0x96] = self._xchga
        m[0x97] = self._xchga

        m[0x01] = self._addregrd16
        m[0x11] = self._adcregrd16
        m[0x03] = self._addregwr16
        m[0x13] = self._adcregwr16
        m[0x02] = self._addregwr8
        m[0x12] = self._adcregwr8
        m[0x05] = self._addax
        m[0x04] = self._addal
        m[0x14] = self._adcal

        m[0x2b] = self._subregwr16
        m[0x1b] = self._sbbregwr16
        m[0x28] = self._subregrd8
        m[0x2a] = self._subregwr8
        m[0x2d] = self._subax
        m[0x2c] = self._subal

        m[0x3b] = self._cmpregto16
        m[0x3a] = self._cmpregto8
        m[0x39] = self._cmpregfrom16
        m[0x38] = self._cmpregfrom8
        m[0x3d] = self._cmpax
        m[0x3c] = self._cmpal

        m[0x27] = self._daa
        m[0xd4] = self._aam
        m[0xd5] = self._aad

        m[0x22] = self._andregwr8
        m[0x20] = self._andregrd8
        m[0x25] = self._andax
        m[0x24] = self._andal

        m[0x0b] = self._orregwr16
        m[0x0a] = self._orregwr8
        m[0x08] = self._orregrd8
        m[0x0d] = self._orax
        m[0x0c] = self._oral

        m[0x33] = self._xorregwr16
        m[0x32] = self._xorregwr8
        m[0x30] = self._xorregrd8
        m[0x34] = self._xoral

        m[0x84] = self._testregto8
        m[0xa8] = self._testal

        m[0xd1] = self._log16
        m[0xd3] = self._log16
        m[0xd0] = self._log8
        m[0xd2] = self._log8

        m[0x40] = self._incax
        m[0x41] = self._inccx
        m[0x42] = self._incdx
        m[0x43] = self._incbx
        m[0x44] = self._incsp
        m[0x45] = self._incbp
        m[0x46] = self._incsi
        m[0x47] = self._incdi

        m[0x48] = self._decax
        m[0x49] = self._deccx
        m[0x4a] = self._decdx
        m[0x4b] = self._decbx
        m[0x4c] = self._decsp
        m[0x4d] = self._decbp
        m[0x4e] = self._decsi
        m[0x4f] = self._decdi

        m[0x81] = self._imm16
        m[0x83] = self._imm16
        m[0x80] = self._imm8

        m[0x98] = self._cbwal
        m[0x99] = self._cwdax

        m[0xe8] = self._call
        m[0x9a] = self._callf
        
        m[0xc3] = self._ret
        m[0xc2] = self._retn
        m[0xcb] = self._retf
        m[0xca] = self._retfn

        m[0xcd] = self._intn
        m[0xcf] = self._iret

        m[0xe9] = self._jmp
        m[0xeb] = self._jmps
        m[0xea] = self._jmpf

        m[0x74] = self._jz
        m[0x75] = self._jnz
        m[0x73] = self._jnc
        m[0x7b] = self._jnp
        m[0x79] = self._jns
        m[0x71] = self._jno
        m[0x76] = self._jbe
        m[0x78] = self._js
        m[0x7a] = self._jp
        m[0x70] = self._jo
        m[0x72] = self._jc
        m[0x7e] = self._jle
        m[0x77] = self._jnbe
        m[0x7c] = self._jnae
        m[0xe3] = self._jcxz

        m[0xe2] = self._loop
        m[0xe0] = self._loopc
        m[0xe1] = self._loopc
        m[0xf2] = self._rep
        m[0xf3] = self._rep

        m[0xf9] = self._stc
        m[0xfd] = self._std
        m[0xfb] = self._sti
        m[0xf8] = self._clc
        m[0xfa] = self._cli
        m[0xfc] = self._cld
        m[0xf5] = self._cmc
        
        m[0x9e] = self._sahf
        m[0x9f] = self._lahf

        m[0xf7] = self._opf7
        m[0xf6] = self._opf6
        m[0xfe] = self._opfe
        m[0xff] = self._opff

        m[0x26] = self._ordes
        m[0x2e] = self._ordcs
        m[0x36] = self._ordss
        m[0x3e] = self._ordds
        

    def _reset(self):
        self._ptr_offset_cache = None
        self._ptr_pci_cache = None
        
        self._ord_seg = None
        self._ord_clear = False
        
        self._rep_op = None
        self._rep_zero = False
        self._rep_start = False
        self._rep_chk = False
        
        self._flags.i = False
        
        self._ip = 0xfff0
        self._cs = 0xf000
        self._flush_iq()

    def _check_break(self, blist):
        return ((self._cs << 4) + self._ip) in blist
            
    def _disable_log(self):
        self._mem.disable_trc()
        self._io.disable_trc()
        
    def _enable_log(self):
        self._mem.enable_trc()
        self._io.enable_trc()

    def _step(self):
        self._fill_iq()
        op = self._fetch()
        f = self._op_map[op]
        if f is None:
            print("unknown opcode %02x" % op)
            self.halt()
            return
        pci = f(op)
        if self._ord_clear:
            self._ord_seg = None
            self._ord_clear = False
        if self._rep_op is not None:
            if self._rep_start:
                self._rep_start = False
                if self._cx == 0x0000:
                    self._rep_op = None
                    pci += 1
            else:
                x = (self._cx - 1) & 0xffff
                if x == 0x0000:
                    self._rep_op = None
                if self._rep_chk:
                    if self._rep_zero and (not self._flags.z):
                        self._rep_op = None
                    elif (not self._rep_zero) and self._flags.z:
                        self._rep_op = None
                self._cx = x
        if self._rep_op is None:
            self._ip = (self._ip + pci) & 0xffff

    def _intr(self):
        #print("intr %02x" % self.ivec)
        if     (not self._flags.i) or \
               (self._rep_op is not None) or \
               (self._ord_seg is not None):
            #print("intr defer %02x" % self.ivec)
            return
        sp = self._sp
        ss = self._n_ss
        vec = self.ivec << 2
        mr = self._mem.read16le
        dw = self._data_write16
        dw(ss, sp - 2, self._get_flags())
        dw(ss, sp - 4, self._cs)
        dw(ss, sp - 6, self._ip)
        self._sp = (sp - 6) & 0xffff
        self._ip = mr(vec)
        self._cs = mr(vec + 2)
        self._flags.i = False
        self._flush_iq()
        self.ivec = None

    def _nop(self, op):
        return 1

    def _hlt(self, op):
        self.halt()
        return 0

    def _stc(self, op):
        self._flags.c = True
        return 1

    def _std(self, op):
        self._flags.d = True
        return 1

    def _sti(self, op):
        self._flags.i = True
        return 1

    def _clc(self, op):
        self._flags.c = False
        return 1

    def _cld(self, op):
        self._flags.d = False
        return 1

    def _cli(self, op):
        self._flags.i = False
        return 1

    def _cmc(self, op):
        self._flags.c = not self._flags.c
        return 1

    def _sahf(self, op):
        self._put_flags(self._ah)
        return 1

    def _lahf(self, op):
        self._ah = self._get_flags() & 0xff
        return 1

    def _movregrd16(self, op):
        modrm = self._fetch()
        pci = self._write_rm16(modrm, self._reg_read16((modrm >> 3) & 0x07), True)
        return pci + 2

    def _movregwr16(self, op):
        modrm = self._fetch()
        (pci, value) = self._read_rm16(modrm)
        self._reg_write16((modrm >> 3) & 0x07, value)
        return pci + 2

    def _movregrd8(self, op):
        modrm = self._fetch()
        pci = self._write_rm8(modrm, self._reg_read8((modrm >> 3) & 0x07), True)
        return pci + 2

    def _movregwr8(self, op):
        modrm = self._fetch()
        (pci, value) = self._read_rm8(modrm)
        self._reg_write8((modrm >> 3) & 0x07, value)
        return pci + 2

    def _movi16(self, op):
        fe = self._fetch
        modrm = fe()
        if modrm & 0x38:
            print("unknown modrm movi16: %02x" % modrm)
            self.halt()
            return 0
        (pci, y) = self._read_rm16(modrm)
        self._write_rm16(modrm, fe() + (fe() << 8), False)
        return pci + 4

    def _movi8(self, op):
        fe = self._fetch
        modrm = fe()
        if modrm & 0x38:
            print("ERROR: unknown modrm movi8: %02x" % modrm)
            self.halt()
            return 0
        (pci, y) = self._read_rm8(modrm)
        self._write_rm8(modrm, fe(), False)
        return pci + 3

    def _movsegrd(self, op):
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x03
        value = self._seg_read(reg)
        pci = self._write_rm16(modrm, value, True)
        return pci + 2

    def _movsegwr(self, op):
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x03
        (pci, value) = self._read_rm16(modrm)
        self._seg_write(reg, value)
        return pci + 2

    def _movaxwr(self, op):
        if self._ord_seg is not None:
            seg = self._ord_seg
        else:
            seg = self._n_ds
        self._ord_clear = True
        fe = self._fetch
        self._ax = self._data_read16(seg, fe() + (fe() << 8))
        return 3

    def _movaxrd(self, op):
        if self._ord_seg is not None:
            seg = self._ord_seg
        else:
            seg = self._n_ds
        self._ord_clear = True
        fe = self._fetch
        self._data_write16(seg, fe() + (fe() << 8), self._ax)
        return 3

    def _movalwr(self, op):
        if self._ord_seg is not None:
            seg = self._ord_seg
        else:
            seg = self._n_ds
        self._ord_clear = True
        fe = self._fetch
        self._al = self._data_read8(seg, fe() + (fe() << 8))
        return 3

    def _movalrd(self, op):
        if self._ord_seg is not None:
            seg = self._ord_seg
        else:
            seg = self._n_ds
        self._ord_clear = True
        fe = self._fetch
        self._data_write8(seg, fe() + (fe() << 8), self._al)
        return 3

    def _in8(self, op):
        self._al = self._io.read8(self._fetch())
        return 2

    def _out8(self, op):
        self._io.write8(self._fetch(), self._al)
        return 2

    def _invar8(self, op):
        self._al = self._io.read8(self._dx)
        return 1

    def _outvar8(self, op):
        self._io.write8(self._dx, self._al)
        return 1

    def _stos16(self, op):
        di = self._di
        self._data_write16(self._n_es, di, self._ax)
        if self._flags.d:
            self._di = (di - 2) & 0xffff
        else:
            self._di = (di + 2) & 0xffff
        return 1

    def _stos8(self, op):
        di = self._di
        self._data_write8(self._n_es, di, self._al)
        if self._flags.d:
            self._di = (di - 1) & 0xffff
        else:
            self._di = (di + 1) & 0xffff
        return 1

    def _movs16(self, op):
        di = self._di
        si = self._si
        self._data_write16(self._n_es, di, self._data_read16(self._n_ds, si))
        if self._flags.d:
            self._si = (si - 2) & 0xffff
            self._di = (di - 2) & 0xffff
        else:
            self._si = (si + 2) & 0xffff
            self._di = (di + 2) & 0xffff
        return 1
        
    def _movs8(self, op):
        di = self._di
        si = self._si
        self._data_write8(self._n_es, di, self._data_read8(self._n_ds, si))
        if self._flags.d:
            self._si = (si - 1) & 0xffff
            self._di = (di - 1) & 0xffff
        else:
            self._si = (si + 1) & 0xffff
            self._di = (di + 1) & 0xffff
        return 1
        
    def _lods16(self, op):
        si = self._si
        self._ax = self._data_read16(self._n_ds, si)
        if self._flags.d:
            self._si = (si - 2) & 0xffff
        else:
            self._si = (si + 2) & 0xffff
        return 1

    def _lods8(self, op):
        si = self._si
        self._al = self._data_read8(self._n_ds, si)
        if self._flags.d:
            self._si = (si - 1) & 0xffff
        else:
            self._si = (si + 1) & 0xffff
        return 1
        
    def _cmps16(self, op):
        di = self._di
        si = self._si
        dr = self._data_read16
        x = dr(self._n_ds, si)
        y = dr(self._n_es, di)
        t = x - y
        flags = self._flags
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        self._set_flags16(t & 0xffff)
        self._rep_chk = True
        if flags.d:
            self._si = (si - 2) & 0xffff
            self._di = (di - 2) & 0xffff
        else:
            self._si = (si + 2) & 0xffff
            self._di = (di + 2) & 0xffff
        return 1
        
    def _cmps8(self, op):
        di = self._di
        si = self._si
        dr = self._data_read8
        x = dr(self._n_ds, si)
        y = dr(self._n_es, di)
        t = x - y
        flags = self._flags
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        self._set_flags8(t & 0xff)
        self._rep_chk = True
        if flags.d:
            self._si = (si - 1) & 0xffff
            self._di = (di - 1) & 0xffff
        else:
            self._si = (si + 1) & 0xffff
            self._di = (di + 1) & 0xffff
        return 1
        
    def _scas16(self, op):
        di = self._di
        x = self._ax
        y = self._data_read16(self._n_es, di)
        t = x - y
        flags = self._flags
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        self._set_flags16(t & 0xff)
        self._rep_chk = True
        if flags.d:
            self._di = (di - 2) & 0xffff
        else:
            self._di = (di + 2) & 0xffff
        return 1
        
    def _scas8(self, op):
        di = self._di
        x = self._al
        y = self._data_read8(self._n_es, di)
        t = x - y
        flags = self._flags
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        self._set_flags8(t & 0xff)
        self._rep_chk = True
        if flags.d:
            self._di = (di - 1) & 0xffff
        else:
            self._di = (di + 1) & 0xffff
        return 1
        
    def _xlat(self, op):
        self._al = self._data_read8(self._n_ds, self._bx + self._al)
        return 1

    def _lds(self, op):
        modrm = self._fetch()
        (pci, offset, seg) = self._ptr_read16(modrm & 0xc0,
                                              modrm & 0x07,
                                              True)
        self._reg_write16((modrm & 0x38) >> 3, offset)
        self._ds = seg
        return pci + 2
        
    def _les(self, op):
        modrm = self._fetch()
        (pci, offset, seg) = self._ptr_read16(modrm & 0xc0,
                                              modrm & 0x07,
                                              True)
        self._reg_write16((modrm & 0x38) >> 3, offset)
        self._es = seg
        return pci + 2
        
    def _xchg16(self, op):
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        (pci, y) = self._read_rm16(modrm)
        self._write_rm16(modrm, self._reg_read16(reg), False)
        self._reg_write16(reg, y)
        return pci + 2

    def _xchg8(self, op):
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        (pci, y) = self._read_rm8(modrm)
        self._write_rm8(modrm, self._reg_read8(reg), False)
        self._reg_write8(reg, y)
        return pci + 2
        
    def _xchga(self, op):
        reg = op & 0x07
        y = self._reg_read16(reg)
        self._reg_write16(reg, self._ax)
        self._ax = y
        return 1
        
    def _addregrd16(self, op):
        flags = self._flags
        modrm = self._fetch()
        (pci, x) = self._read_rm16(modrm)
        y = self._reg_read16((modrm >> 3) & 0x07)
        t = x + y
        flags.c = (t > 0xffff)
        flags.a = (((x & 0x0f) + (y & 0x0f)) > 0x0f)
        t &= 0xffff
        self._write_rm16(modrm, t, False)
        self._set_flags16(t)
        return pci + 2

    def _adcregrd16(self, op):
        flags = self._flags
        modrm = self._fetch()
        (pci, x) = self._read_rm16(modrm)
        y = self._reg_read16((modrm >> 3) & 0x07)
        c = int(flags.c)
        t =  x + y + c
        flags.c = (t > 0xffff)
        flags.a = (((x & 0x0f) + (y & 0x0f) + c) > 0x0f)
        t &= 0xffff
        self._write_rm16(modrm, t, False)
        self._set_flags16(t)
        return pci + 2

    def _addregwr16(self, op):
        flags = self._flags
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        x = self._reg_read16(reg)
        (pci, y) = self._read_rm16(modrm)
        t = x + y
        flags.c = (t > 0xffff)
        flags.a = (((x & 0x0f) + (y & 0x0f)) > 0x0f)
        t &= 0xffff
        self._reg_write16(reg, t)
        self._set_flags16(t)
        return pci + 2

    def _adcregwr16(self, op):
        flags = self._flags
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        x = self._reg_read16(reg)
        (pci, y) = self._read_rm16(modrm)
        c = int(flags.c)
        t = x + y + c
        flags.c = (t > 0xffff)
        flags.a = (((x & 0x0f) + (y & 0x0f) + c) > 0x0f)
        t &= 0xffff
        self._reg_write16(reg, t)
        self._set_flags16(t)
        return pci + 2

    def _addregwr8(self, op):
        flags = self._flags
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        x = self._reg_read8(reg)
        (pci, y) = self._read_rm8(modrm)
        t = x + y
        flags.c = (t > 0xff)
        flags.a = (((x & 0x0f) + (y & 0x0f)) > 0x0f)
        t &= 0xff
        self._reg_write8(reg, t)
        self._set_flags8(t)
        return pci + 2

    def _adcregwr8(self, op):
        flags = self._flags
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        x = self._reg_read8(reg)
        (pci, y) = self._read_rm8(modrm)
        c = int(flags.c)
        t = x + y + c
        flags.c = (t > 0xff)
        flags.a = (((x & 0x0f) + (y & 0x0f) + c) > 0x0f)
        t &= 0xff
        self._reg_write8(reg, t)
        self._set_flags8(t)
        return pci + 2

    def _addax(self, op):
        flags = self._flags
        fe = self._fetch
        x = self._ax
        y = fe() + (fe() << 8)
        t = x + y
        flags.c = (t > 0xffff)
        flags.a = (((x & 0x0f) + (y & 0x0f)) > 0x0f)
        t &= 0xffff
        self._ax = t
        self._set_flags16(t)
        return 3

    def _addal(self, op):
        flags = self._flags
        x = self._al
        y = self._fetch()
        t = x + y
        flags.c = (t > 0xff)
        flags.a = (((x & 0x0f) + (y & 0x0f)) > 0x0f)
        t &= 0xff
        self._al = t
        self._set_flags8(t)
        return 2

    def _adcal(self, op):
        flags = self._flags
        x = self._al
        y = self._fetch()
        c = int(flags.c)
        t = x + y + c
        flags.c = (t > 0xff)
        flags.a = (((x & 0x0f) + (y & 0x0f) + c) > 0x0f)
        t &= 0xff
        self._al = t
        self._set_flags8(t)
        return 2

    def _subregwr16(self, op):
        flags = self._flags
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        x = self._reg_read16(reg)
        (pci, y) = self._read_rm16(modrm)
        t = x - y
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        t &= 0xffff
        self._reg_write16(reg, t)
        self._set_flags16(t)
        return pci + 2
        
    def _sbbregwr16(self, op):
        flags = self._flags
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        x = self._reg_read16(reg)
        (pci, y) = self._read_rm16(modrm)
        c = int(flags.c)
        t = x - y - c
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f) - c) < 0)
        t &= 0xffff
        self._reg_write16(reg, t)
        self._set_flags16(t)
        return pci + 2
        
    def _subregrd8(self, op):
        flags = self._flags
        modrm = self._fetch()
        (pci, x) = self._read_rm8(modrm)
        y = self._reg_read8((modrm >> 3) & 0x07)
        t = x - y
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        t &= 0xff
        self._write_rm8(modrm, t, False)
        self._set_flags8(t)
        return pci + 2

    def _subregwr8(self, op):
        flags = self._flags
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        x = self._reg_read8(reg)
        (pci, y) = self._read_rm8(modrm)
        t = x - y
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        t &= 0xff
        self._reg_write8(reg, t)
        self._set_flags8(t)
        return pci + 2
        
    def _subax(self, op):
        flags = self._flags
        fe = self._fetch
        x = self._ax
        y = fe() + (fe() << 8)
        t = x - y
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        t &= 0xffff
        self._ax = t
        self._set_flags16(t)
        return 3
        
    def _subal(self, op):
        flags = self._flags
        x = self._al
        y = self._fetch()
        t = x - y
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        t &= 0xff
        self._al = t
        self._set_flags8(t)
        return 2

    def _cmpregto16(self, op):
        flags = self._flags
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        x = self._reg_read16(reg)
        (pci, y) = self._read_rm16(modrm)
        t = x - y
        tc = (x & 0x0f) - (y & 0x0f)
        flags.c = (t < 0)
        flags.a = (tc < 0)
        self._set_flags16(t & 0xffff)
        return pci + 2

    def _cmpregto8(self, op):
        flags = self._flags
        modrm = self._fetch() 
        x = self._reg_read8((modrm >> 3) & 0x07)
        (pci, y) = self._read_rm8(modrm)
        t = x - y 
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        self._set_flags8(t & 0xff)
        return pci + 2
        
    def _cmpregfrom16(self, op):
        flags = self._flags
        modrm = self._fetch()
        (pci, x) = self._read_rm16(modrm)
        y = self._reg_read16((modrm >> 3) & 0x07)
        t = x - y
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        self._set_flags16(t & 0xffff)
        return pci + 2

    def _cmpregfrom8(self, op):
        flags = self._flags
        modrm = self._fetch()
        (pci, x) = self._read_rm8(modrm)
        y = self._reg_read8((modrm >> 3) & 0x07)
        t = x - y
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        self._set_flags8(t & 0xff)
        return pci + 2

    def _cmpax(self, op):
        flags = self._flags
        fe = self._fetch
        y = fe() + (fe() << 8)
        x = self._ax
        t = x - y
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        self._set_flags16(t & 0xffff)
        return 3

    def _cmpal(self, op):
        flags = self._flags
        x = self._al
        y = self._fetch()
        t = x - y 
        flags.c = (t < 0)
        flags.a = (((x & 0x0f) - (y & 0x0f)) < 0)
        self._set_flags8(t & 0xff)
        return 2

    def _daa(self, op):
        f = self._flags
        t = self._al
        if ((t & 0x0f) > 9) or f.a:
            t  = (t + 0x06) & 0xff
            f.a = True
        else:
            f.a = False
        if (t > 0x9f) or f.c:
            t = (t + 0x60) & 0xff
            f.c = True
        else:
            f.c = False
        self._al = t
        self._set_flags8(t)
        return 1
        
    def _aam(self, op):
        modrm = self._fetch()
        if modrm != 0x0a:
            print("ERROR: AAM unknown modrm %02x" % modrm)
            self.halt()
            return 0
        t = self._al
        self._ah = (t // 10) & 0xff
        self._al = t = (t % 10) & 0xff
        self._set_flags8(t)
        return 2
        
    def _aad(self, op):
        modrm = self._fetch()
        if modrm != 0x0a:
            print("ERROR: AAM unknown modrm %02x" % modrm)
            self.halt()
            return 0 
        t = ((self._ah * 10) + self._al) & 0xff
        self._al = t
        self._ah = 0x00
        self._set_flags8(t)
        return 2

    def _andregwr8(self, op):
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        f = self._flags
        (pci, y) = self._read_rm8(modrm)
        t = self._reg_read8(reg) & y
        self._reg_write8(reg, t)
        f.c = f.o = False
        self._set_flags8(t)
        return pci + 2
        
    def _andregrd8(self, op):
        modrm = self._fetch()
        f = self._flags
        (pci, x) = self._read_rm8(modrm)
        t = self._reg_read8((modrm >> 3) & 0x07) & x
        self._write_rm8(modrm, t, False)
        f.c = f.o = False
        self._set_flags8(t)
        return pci + 2

    def _andax(self, op):
        f = self._flags
        fe = self._fetch
        self._ax = t = self._ax & (fe() + (fe() << 8))
        f.c = f.o = False
        self._set_flags16(t)
        return 3

    def _andal(self, op):
        self._al = t = self._al & self._fetch()
        f = self._flags
        f.c = f.o = False
        self._set_flags8(t)
        return 2

    def _orregwr16(self, op):
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        f = self._flags
        (pci, y) = self._read_rm16(modrm)
        t = self._reg_read16(reg) | y
        self._reg_write16(reg, t)
        f.c = f.o = False
        self._set_flags16(t)
        return pci + 2

    def _orregwr8(self, op):
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        f = self._flags
        (pci, y) = self._read_rm8(modrm)
        t = self._reg_read8(reg) | y
        self._reg_write8(reg, t)
        f.c = f.o = False
        self._set_flags8(t)
        return pci + 2
        
    def _orregrd8(self, op):
        modrm = self._fetch()
        f = self._flags
        (pci, x) = self._read_rm8(modrm)
        t = self._reg_read8((modrm >> 3) & 0x07) | x
        self._write_rm8(modrm, t, False)
        f.c = f.o = False
        self._set_flags8(t)
        return pci + 2

    def _orax(self, op):
        flags = self._flags
        fe = self._fetch
        self._ax = t = self._ax | (fe() + (fe() << 8))
        flags.c = flags.o = False
        self._set_flags16(t)
        return 3

    def _oral(self, op):
        self._al = t = self._al | self._fetch()
        f = self._flags
        f.c = f.o = False
        self._set_flags8(t)
        return 2

    def _xorregwr16(self, op):
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        f = self._flags
        (pci, y) = self._read_rm16(modrm)
        t = self._reg_read16(reg) ^ y
        self._reg_write16(reg, t)
        f.c = f.o = False
        self._set_flags16(t)
        return pci + 2

    def _xorregwr8(self, op):
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        f = self._flags
        (pci, y) = self._read_rm8(modrm)
        t = self._reg_read8(reg) ^ y
        self._reg_write8(reg, t)
        f.c = f.o = False
        self._set_flags8(t)
        return pci + 2
        
    def _xorregrd8(self, op):
        modrm = self._fetch() 
        f = self._flags
        (pci, x) = self._read_rm8(modrm)
        t = self._reg_read8((modrm >> 3) & 0x07) ^ x
        self._write_rm8(modrm, t, False)
        f.c = f.o = False
        self._set_flags8(t)
        return pci + 2
        
    def _xoral(self, op):
        self._al = t = self._al ^ self._fetch()
        f = self._flags
        f.c = f.o = False
        self._set_flags8(t)
        return 2
        
    def _testregto8(self, op):
        modrm = self._fetch()
        f = self._flags
        (pci, y) = self._read_rm8(modrm)
        f.c = f.o = False
        self._set_flags8(self._reg_read8((modrm >> 3) & 0x07) & y)
        return pci + 2

    def _testal(self, op):
        f = self._flags
        f.c = f.o = False
        self._set_flags8(self._al & self._fetch())
        return 2

    def _log16(self, op):
        modrm = self._fetch()
        lr = modrm & 0x38
        f = self._flags
        if not (op & 0x02):
            c = 1
            single = True
        else:
            c = self._cl
            single = False
        (pci, x) = self._read_rm16(modrm)
        if lr == 0x20:                              # SHL
            for n in range(c):
                f.c = ((x & 0x8000) != 0x0000)
                x = (x << 1) & 0xffff
            if single:
                f.o = (((x & 0x8000) != 0) != f.c)
        elif lr == 0x28:                            # SHR
            if single:
                f.o = ((x & 0x8000) != 0x0000)
            for n in range(c):
                f.c = ((x & 0x0001) != 0x0000)
                x >>= 1
        elif lr == 0x00:                            # ROL
            for n in range(c):
                f.c = ((x & 0x8000) != 0x0000)
                t = (x & 0x8000) >> 15
                x = ((x << 1) & 0xffff) | t
            if single:
                f.o = (((x & 0x8000) != 0) != f.c)
        elif lr == 0x08:                            # ROR
            for n in range(c):
                f.c = ((x & 0x0001) != 0x0000)
                t = (x & 0x0001) << 15
                x = (x >> 1) | t
            if single:
                f.o = (((x & 0x8000) != 0) != f.c)
        elif lr == 0x38:                            # SAR
            t = x & 0x8000
            for n in range(c):
                f.c = ((x & 0x0001) != 0x0000)
                x = (x >> 1) | t
            if single:
                f.o = False   
        elif lr == 0x10:                            # RCL
            for n in range(c):
                savec = f.c
                f.c = ((x & 0x8000) != 0x0000)
                x = (x << 1) & 0xffff
                if savec:
                    x |= 0x0001
            if single:
                f.o = (((x & 0x8000) != 0) != f.c)
        else:
            print("unknown modrm: %02x, imm lr=%02x" % (modrm, lr))
            self.halt()
            return 0
        self._write_rm16(modrm, x, False)
        self._set_flags16(x)
        return pci + 2

    def _log8(self, op):
        modrm = self._fetch()
        lr = modrm & 0x38
        f = self._flags
        if not (op & 0x02):
            c = 1
            single = True
        else:
            c = self._cl
            single = False
        (pci, x) = self._read_rm8(modrm)
        if lr == 0x20:                              # SHL
            for n in range(c):
                f.c = ((x & 0x80) != 0x00)
                x = (x << 1) & 0xffff
            if single:
                f.o = (((x & 0x80) != 0) != f.c)
        elif lr == 0x28:                            # SHR
            for n in range(c):
                f.c = ((x & 0x01) != 0x00)
                x >>= 1
        elif lr == 0x00:                            # ROL
            for n in range(c):
                f.c = ((x & 0x80) != 0x00)
                t = (x & 0x80) >> 7
                x = ((x << 1) & 0xff) | t
            if single:
                f.o = (((x & 0x80) != 0) != f.c)
        elif lr == 0x08:                            # ROR
            for n in range(c):
                f.c = ((x & 0x01) != 0x00)
                t = (x & 0x01) << 7
                x = (x >> 1) | t
            if single:
                f.o = (((x & 0x80) != 0) != f.c)
        elif lr == 0x38:                            # SAR
            t = x & 0x80
            for n in range(c):
                f.c = ((x & 0x01) != 0x00)
                x = (x >> 1) | t
            if single:
                f.o = False
        else:
            print("unknown modrm: %02x, imm lr=%02x" % (modrm, lr))
            self.halt()
            return 0
        self._write_rm8(modrm, x, False)
        self._set_flags8(x)
        return pci + 2
        
    def _imm16(self, op):
        fe = self._fetch
        modrm = fe()
        f = self._flags
        ar = modrm & 0x38
        (cpci, r) = self._read_rm16(modrm)
        x = fe()
        if not (op & 0x02):
            x += (fe() << 8)
            pci = 4
        else:
            if x > 0x7f:
                x = -((-x) & 0xff)
            pci = 3
        if ar == 0x00:                          # ADD
            s = r + x
            f.c = (s > 0xffff)
            f.a = (((r & 0x0f) + (x & 0x0f)) > 0x0f)
            s &= 0xffff
        elif ar == 0x10:                        # ADC
            c = int(f.c)
            s = r + x + c
            f.c = (s > 0xffff)
            f.a = (((r & 0x0f) + (x & 0x0f) + c) > 0x0f)
            s &= 0xffff
        elif ar == 0x28:                        # SUB
            s = r - x
            f.c = (s < 0)
            f.a = (((r & 0x0f) - (x & 0x0f)) < 0)
            s &= 0xffff
        elif ar == 0x38:                        # CMP
            s = r - x
            f.c = (s < 0)
            f.a = (((r & 0x0f) - (x & 0x0f)) < 0)
            s &= 0xffff
        elif ar == 0x20:                        # AND
            s = r & x
            f.c = f.o = False
        else:
            print("unknown modrm: %02x, imm16 ar=%02x" % (modrm, ar))
            self.halt()
            return 0
        if ar != 0x38:
            self._write_rm16(modrm, s, False)
        self._set_flags16(s)
        return pci + cpci

    def _imm8(self, op):
        fe = self._fetch
        modrm = fe()
        f = self._flags
        ar = modrm & 0x38
        (cpci, r) = self._read_rm8(modrm)
        x = fe()
        if ar == 0x00:                          # ADD
            s = r + x
            f.c = (s > 0xff)
            f.a = (((r & 0x0f) + (x & 0x0f)) > 0x0f)
            s &= 0xff
        elif ar == 0x10:                        # ADC
            c = int(f.c)
            s = r + x + c
            f.c = (s > 0xff)
            f.a = (((r & 0x0f) + (x & 0x0f) + c) > 0x0f)
            s &= 0xff
        elif ar == 0x38:                        # CMP
            s = r - x
            f.c = (s < 0)
            f.a = (((r & 0x0f) - (x & 0x0f)) < 0)
            s &= 0xff
        elif ar == 0x20:                        # AND
            s = r & x
            f.c = f.o = False
        elif ar == 0x08:                        # OR
            s = r | x
            f.c = f.o = False
        elif ar == 0x30:                        # XOR
            s = r ^ x
            f.c = f.o = False
        else:
            print("unknown modrm: %02x, imm8 ar=%02x" % (modrm, ar))
            self.halt()
            return 0
        if ar != 0x38:
            self._write_rm8(modrm, s, False)
        self._set_flags8(s)
        return 3 + cpci

    def _opf7(self, op):
        modrm = self._fetch()
        pr = modrm & 0x38
        f = self._flags
        (pci, x) = self._read_rm16(modrm)
        if pr == 0x10:                          # NOT
            x = (~x) & 0xffff
            self._write_rm16(modrm, x, False)
        elif pr == 0x18:                        # NEG
            f.c = (x != 0x0000)
            x = (0 - x) & 0xffff
            self._write_rm16(modrm, x, False)
            self._set_flags16(x)
        elif pr == 0x00:                        # TEST
            t = x & (self._fetch() + (self._fetch() << 8))
            f.c = f.o = False
            self._set_flags16(t)
            pci += 2
        elif pr == 0x20:                        # MUL
            t = self._ax * x
            self._ax = t & 0xffff
            self._dx = (t >> 16) & 0xffff
            f.c = f.o = (self._dx != 0x0000)
        elif pr == 0x30:                        # DIV
            y = (self._dx << 16) + self._ax
            self._ax = y // x
            self._dx = y % x
        else:
            print("unknown modrm: %02x, f7 pr=%02x" % (modrm, pr))
            self.halt()
            return 0
        return pci + 2

    def _opf6(self, op):
        modrm = self._fetch()
        pr = modrm & 0x38
        f = self._flags
        (pci, x) = self._read_rm8(modrm)
        if pr == 0x10:                          # NOT
            x = (~x) & 0xff
            self._write_rm8(modrm, x, False)
        elif pr == 0x18:                        # NEG
            f.c = (x != 0x00)
            x = (0 - x) & 0xff
            self._write_rm8(modrm, x, False)
            self._set_flags8(x)
        elif pr == 0x00:                        # TEST
            x &= self._fetch()
            f.c = f.o = False
            self._set_flags8(x)
            pci += 1
        elif pr == 0x20:                        # MUL
            self._ax = (self._al * x) & 0xffff
            f.c = f.o = (self._ah != 0x00)
        elif pr == 0x30:                        # DIV
            y = self._ax
            self._al = y // x
            self._ah = y % x
        else:
            print("unknown modrm: %02x, f6 pr=%02x" % (modrm, pr))
            self.halt()
            return 0
        return pci + 2

    def _opfe(self, op):
        modrm = self._fetch()
        pr = modrm & 0x38
        (pci, x) = self._read_rm8(modrm)
        if pr == 0x00:                          # INC
            x = (x + 1) & 0xff
        elif pr == 0x08:                        # DEC
            x = (x - 1) & 0xff
        else:
            print("unknown modrm: %02x, fe pr=%02x" % (modrm, pr))
            self.halt()
            return 0
        self._write_rm8(modrm, x, False)
        self._set_flags8(x)
        return pci + 2

    def _opff(self, op):
        modrm = self._fetch()
        cr = modrm & 0x38
        if (cr == 0x18) or (cr == 0x28):
            (pci, x, x1) = self._ptr_read16(modrm & 0xc0, modrm & 0x07, True)
        else:
            (pci, x) = self._read_rm16(modrm)
        if cr == 0x20:                          # JMP
            self._ip = x
            self._flush_iq()
            return 0
        elif cr == 0x00:                        # INC
            x = (x + 1) & 0xffff
            self._write_rm16(modrm, x, False)
            self._set_flags16(x)
        elif cr == 0x30:                        # PUSH
            sp = (self._sp - 2) & 0xffff
            self._data_write16(self._n_ss, sp, x)
            self._sp = sp
        elif cr == 0x10:                        # CALL
            sp = (self._sp - 2) & 0xffff
            self._data_write16(self._n_ss, sp, (self._ip + 2 + pci) & 0xffff)
            self._ip = x
            self._sp = sp
            self._flush_iq()
            return 0
        elif cr == 0x18:                        # CALLF
            ss = self._n_ss
            dw = self._data_write16
            sp = (self._sp - 4) & 0xffff
            dw(ss, sp + 2, self._cs)
            dw(ss, sp, (self._ip + 2 + pci) & 0xffff)
            self._ip = x
            self._cs = x1
            self._sp = sp
            self._flush_iq()
            return 0
        elif cr == 0x28:                        # JMPF
            self._ip = x
            self._cs = x1
            self._flush_iq()
            return 0
        else:
            print("unknown modrm: %02x, ff cr=%02x" % (modrm, cr))
            self.halt()
            return 0
        return pci + 2
        
    def _moviax(self, op):
        self._ax = self._fetch() + (self._fetch() << 8)
        return 3

    def _movibx(self, op):
        self._bx = self._fetch() + (self._fetch() << 8)
        return 3

    def _movicx(self, op):
        self._cx = self._fetch() + (self._fetch() << 8)
        return 3

    def _movidx(self, op):
        self._dx = self._fetch() + (self._fetch() << 8)
        return 3

    def _movisp(self, op):
        self._sp = self._fetch() + (self._fetch() << 8)
        return 3

    def _movibp(self, op):
        self._bp = self._fetch() + (self._fetch() << 8)
        return 3

    def _movisi(self, op):
        self._si = self._fetch() + (self._fetch() << 8)
        return 3

    def _movidi(self, op):
        self._di = self._fetch() + (self._fetch() << 8)
        return 3

    def _movial(self, op):
        self._al = self._fetch()
        return 2

    def _moviah(self, op):
        self._ah = self._fetch()
        return 2

    def _movibl(self, op):
        self._bl = self._fetch()
        return 2

    def _movibh(self, op):
        self._bh = self._fetch()
        return 2

    def _movicl(self, op):
        self._cl = self._fetch()
        return 2

    def _movich(self, op):
        self._ch = self._fetch()
        return 2

    def _movidl(self, op):
        self._dl = self._fetch()
        return 2

    def _movidh(self, op):
        self._dh = self._fetch()
        return 2

    def _pushax(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._ax)
        return 1

    def _pushbx(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._bx)
        return 1

    def _pushcx(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._cx)
        return 1

    def _pushdx(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._dx)
        return 1

    def _pushbp(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._bp)
        return 1

    def _pushsi(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._si)
        return 1

    def _pushdi(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._di)
        return 1

    def _pushes(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._es)
        return 1

    def _pushds(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._ds)
        return 1

    def _pushss(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._ss)
        return 1

    def _pushcs(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._cs)
        return 1

    def _popax(self, op):
        sp = self._sp
        self._ax = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        return 1

    def _popbx(self, op):
        sp = self._sp
        self._bx = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        return 1

    def _popcx(self, op):
        sp = self._sp
        self._cx = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        return 1

    def _popdx(self, op):
        sp = self._sp
        self._dx = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        return 1

    def _popbp(self, op):
        sp = self._sp
        self._bp = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        return 1

    def _popsi(self, op):
        sp = self._sp
        self._si = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        return 1

    def _popdi(self, op):
        sp = self._sp
        self._di = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        return 1

    def _popds(self, op):
        sp = self._sp
        self._ds = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        return 1

    def _popes(self, op):
        sp = self._sp
        self._es = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        return 1

    def _popss(self, op):
        sp = self._sp
        self._ss = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        return 1

    def _poprm(self, op):
        modrm = self._fetch()
        if (modrm & 0x38) != 0x00:
            print("unknown modrm poprm %02x" % modrm)
            self.hlt = True
            return 0
        sp = self._sp
        x = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        pci = self._write_rm16(modrm, x, True)
        return pci + 2

    def _pushf(self, op):
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, self._get_flags())
        return 1

    def _popf(self, op):
        sp = self._sp
        self._put_flags(self._data_read16(self._n_ss, sp))
        self._sp = (sp + 2) & 0xffff
        return 1

    def _incax(self, op):
        self._ax = x = (self._ax + 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _incbx(self, op):
        self._bx = x = (self._bx + 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _inccx(self, op):
        self._cx = x = (self._cx + 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _incdx(self, op):
        self._dx = x = (self._dx + 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _incsp(self, op):
        self._sp = x = (self._sp + 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _incbp(self, op):
        self._bp = x = (self._bp + 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _incsi(self, op):
        self._si = x = (self._si + 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _incdi(self, op):
        self._di = x = (self._di + 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _decax(self, op):
        self._ax = x = (self._ax - 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _decbx(self, op):
        self._bx = x = (self._bx - 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _deccx(self, op):
        self._cx = x = (self._cx - 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _decdx(self, op):
        self._dx = x = (self._dx - 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _decsp(self, op):
        self._sp = x = (self._sp - 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _decbp(self, op):
        self._bp = x = (self._bp - 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _decsi(self, op):
        self._si = x = (self._si - 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _decdi(self, op):
        self._di = x = (self._di - 1) & 0xffff
        self._set_flags16(x)
        return 1

    def _cbwal(self, op):
        al = self._al
        if al > 0x7f:
            self._ax = 0xff00 | al
        else:
            self._ax = al
        return 1

    def _cwdax(self, op):
        if self._ax > 0x7fff:
            self._dx = 0xffff
        else:
            self._dx = 0x0000
        return 1

    def _call(self, op):
        ip = self._ip
        fe = self._fetch
        self._sp = sp = (self._sp - 2) & 0xffff
        self._data_write16(self._n_ss, sp, (ip + 3) & 0xffff)
        disp = fe() + (fe() << 8)
        self._ip = (ip + disp + 3) & 0xffff
        self._flush_iq()
        return 0

    def _callf(self, op):
        fe = self._fetch
        ss = self._n_ss
        self._sp = sp = (self._sp - 4) & 0xffff
        dw = self._data_write16
        dw(ss, sp + 2, self._cs)
        dw(ss, sp, (self._ip + 5) & 0xffff)
        self._ip = fe() + (fe() << 8)
        self._cs = fe() + (fe() << 8)
        self._flush_iq()
        return 0

    def _ret(self, op):
        sp = self._sp
        self._ip = self._data_read16(self._n_ss, sp)
        self._sp = (sp + 2) & 0xffff
        self._flush_iq()
        return 0

    def _retn(self, op):
        fe = self._fetch
        so = fe() + (fe() << 8)
        sp = self._sp
        self._ip = self._data_read16(self._n_ss, sp)
        self._sp = (sp + so + 2) & 0xffff
        self._flush_iq()
        return 0

    def _retf(self, op):
        sp = self._sp
        ss = self._n_ss
        dr = self._data_read16
        self._ip = dr(ss, sp)
        self._cs = dr(ss, sp + 2)
        self._sp = (sp + 4) & 0xffff
        self._flush_iq()
        return 0
        
    def _retfn(self, op):
        sp = self._sp
        ss = self._n_ss
        fe = self._fetch
        so = fe() + (fe() << 8)
        dr = self._data_read16
        self._ip = dr(ss, sp)
        self._cs = dr(ss, sp + 2)
        self._sp = (sp + so + 4) & 0xffff
        self._flush_iq()
        return 0

    def _intn(self, op):
        self._do_intr(self._fetch())
        return 0
        
    def _do_intr(self, vec):
        vec <<= 2
        sp = self._sp
        ss = self._n_ss
        dw = self._data_write16
        mr = self._mem.read16le
        dw(ss, sp - 2, self._get_flags())
        dw(ss, sp - 4, self._cs)
        dw(ss, sp - 6, (self._ip + 2) & 0xffff)
        self._sp = (sp - 6) & 0xffff
        self._ip = mr(vec)
        self._cs = mr(vec + 2)
        self._flags.i = False
        self._flush_iq()

    def _iret(self, op):
        sp = self._sp
        ss = self._n_ss
        dr = self._data_read16
        self._ip = dr(ss, sp)
        self._cs = dr(ss, sp + 2)
        self._put_flags(dr(ss, sp + 4))
        self._sp = (sp + 6) & 0xffff
        self._flush_iq()
        return 0

    def _jmp(self, op):
        fe = self._fetch
        offset = fe() + (fe() << 8)
        self._ip = (self._ip + offset + 3) & 0xffff
        self._flush_iq()
        return 0

    def _jmps(self, op):
        disp = self._fetch()
        if disp > 0x7f:
            disp = 2 - ((-disp) & 0xff)
        else:
            disp += 2
        self._ip = (self._ip + disp) & 0xffff
        self._flush_iq()
        return 0

    def _jmpf(self, op):
        fe = self._fetch
        self._ip = fe() + (fe() << 8)
        self._cs = fe() + (fe() << 8)
        self._flush_iq()
        return 0

    def _jz(self, op):
        if self._flags.z:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _jnz(self, op):
        if not self._flags.z:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _jnc(self, op):
        if not self._flags.c:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _jnp(self, op):
        if not self._flags.p:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _jns(self, op):
        if not self._flags.s:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _jno(self, op):
        if not self._flags.o:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _jbe(self, op):
        if self._flags.z or self._flags.c:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _jnae(self, op):
        if (not self._flags.z) and self._flags.c:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci
        
    def _jnbe(self, op):
        if (not self._flags.z) and (not self._flags.c):
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci
        
    def _jle(self, op):
        if self._flags.z or self._flags.s:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _js(self, op):
        if self._flags.s:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _jp(self, op):
        if self._flags.p:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _jc(self, op):
        if self._flags.c:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _jo(self, op):
        if self._flags.o:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _jcxz(self, op):
        if self._cx == 0x0000:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _loop(self, op):
        self._cx = (self._cx - 1) & 0xffff
        if self._cx != 0x0000:
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci
        
    def _loopc(self, op):
        self._cx = (self._cx - 1) & 0xffff
        if not (op & 0x01):
            f = not self._flags.z
        else:
            f = self._flags.z
        if f and (self._cx != 0x0000):
            disp = self._fetch()
            if disp > 0x7f:
                disp = 2 - ((-disp) & 0xff)
            else:
                disp += 2
            self._ip = (self._ip + disp) & 0xffff
            self._flush_iq()
            pci = 0
        else:
            self._fetch()
            pci = 2
        return pci

    def _rep(self, op):
        self._rep_op = self._fetch()
        self._rep_zero = ((op & 0x01) != 0x00)
        self._rep_start = True
        self._rep_chk = False
        self._ip = (self._ip + 1) & 0xffff
        return 0

    def _ordes(self, op):
        self._ord_seg = self._n_es
        return 1

    def _ordcs(self, op):
        self._ord_seg = self._n_cs
        return 1

    def _ordss(self, op):
        self._ord_seg = self._n_ss
        return 1

    def _ordds(self, op):
        self._ord_seg = self._n_ds
        return 1
        
    def _lea(self, op):
        modrm = self._fetch()
        reg = (modrm >> 3) & 0x07
        mod = modrm & 0xc0
        rm = modrm & 0x07
        offset = 0
        if mod == 0x00:
            if rm == 6:
                offset = self._fetch() + (self._fetch() << 8)
                pci = 2
            else:
                offset = 0
                pci = 0
        elif mod == 0x40:
            offset = self._fetch()
            if offset > 0x7f:
                offset = -((-offset) & 0xff)
            pci = 1
        else:
            offset = self._fetch() + (self._fetch() << 8)
            pci = 2
        if rm == 6:
            if mod == 0x00:
                addr = offset
            else:
                addr = self._bp + offset
        elif rm == 7:
            addr = self._bx + offset
        elif rm == 4:
            addr = self._si + offset
        elif rm == 5:
            addr = self._di + offset
        elif rm == 0:
            addr = self._bx + self._si + offset
        elif rm == 1:
            addr = self._bx + self._di + offset
        elif rm == 2:
            addr = self._bp + self._si + offset
        else:
            addr = self._bp + self._di + offset
        self._reg_write16(reg, addr)
        return pci + 2

    def _read_rm16(self, modrm):
        mod = modrm & 0xc0
        rm = modrm & 0x07
        #print("modrm16 %02x %02x" % (mod, rm))
        if mod == 0xc0:
            return (0, self._reg_read16(rm))
        else:
            return self._ptr_read16(mod, rm, False)

    def _write_rm16(self, modrm, value, scanDisp):
        mod = modrm & 0xc0
        rm = modrm & 0x07
        if mod == 0xc0:
            self._reg_write16(rm, value)
            return 0
        else:
            return self._ptr_write16(mod, rm, value, scanDisp)

    def _read_rm8(self, modrm):
        mod = modrm & 0xc0
        rm = modrm & 0x07
        #print("modrm %02x %02x" % (mod, rm))
        if mod == 0xc0:
            return (0, self._reg_read8(rm))
        else:
            return self._ptr_read8(mod, rm)

    def _write_rm8(self, modrm, value, scanDisp):
        mod = modrm & 0xc0
        rm = modrm & 0x07
        if mod == 0xc0:
            self._reg_write8(rm, value)
            return 0
        else:
            return self._ptr_write8(mod, rm, value, scanDisp)

    def _fill_iq(self):
        iq = self._iq
        bc = 6 - len(iq)
        if bc >= 2:
            pf = self._pf
            ca = self._cs << 4
            mem = self._mem
            ap = iq.appendleft
            #print("fill %d %04x" % (bc, pf))
            while bc > 1:
                if pf & 0x0001: 
                    ap(mem.read8(ca + pf))
                    pf = (pf + 1) & 0xffff
                    bc -= 1
                else:
                    x = mem.read16le(ca + pf)
                    ap(x & 0xff)
                    ap(x >> 8)
                    pf = (pf + 2) & 0xffff
                    bc -= 2
            self._pf = pf

    def _flush_iq(self):
        self._iq.clear()
        self._pf = self._ip

    def _fetch(self):
        if self._rep_op is not None:
            return self._rep_op
        iq = self._iq
        if len(iq) == 0:
            self._fill_iq()
        return iq.pop()

    def _data_read16(self, seg, offset):
        addr = (getattr(self, seg) << 4) + offset
        if addr & 0x0001:
            mr = self._mem.read8
            return mr(addr) + (mr(addr + 1) << 8)
        else:
            return self._mem.read16le(addr)

    def _data_write16(self, seg, offset, value):
        addr = (getattr(self, seg) << 4) + offset
        if addr & 0x0001:
            mw = self._mem.write8
            mw(addr, value & 0xff)
            mw(addr + 1, value >> 8)
        else:
            self._mem.write16le(addr, value)

    def _data_read8(self, seg, offset): 
        return self._mem.read8((getattr(self, seg) << 4) + offset)

    def _data_write8(self, seg, offset, value):
        self._mem.write8((getattr(self, seg) << 4) + offset, value)
        
    def _reg_read16(self, reg):
        return getattr(self, self._reg_map16[reg])

    def _reg_write16(self, reg, value):
        setattr(self, self._reg_map16[reg], value)

    def _reg_read8(self, reg):
        return getattr(self, self._reg_map8[reg])

    def _reg_write8(self, reg, value):
        setattr(self, self._reg_map8[reg], value)

    def _seg_read(self, reg):
        return getattr(self, self._seg_map[reg])

    def _seg_write(self, reg, value):
        setattr(self, self._seg_map[reg], value)

    def _ptr_read16(self, mod, rm, double):
        if mod == 0x00:
            if rm == 6:
                offset = self._fetch() + (self._fetch() << 8)
                pci = 2
            else:
                offset = 0
                pci = 0
        elif mod == 0x40:
            offset = self._fetch()
            if offset > 0x7f:
                offset = -((-offset) & 0xff)
            pci = 1
        else: 
            offset = self._fetch() + (self._fetch() << 8)
            pci = 2
        self._ptr_offset_cache = offset
        self._ptr_pci_cache = pci
        self._ord_clear = True
        if rm == 6:
            if mod == 0x00:
                if self._ord_seg is not None:
                    seg = self._ord_seg
                else:
                    seg = self._n_ds
                if double:
                    return (pci, 
                            self._data_read16(seg, offset),
                            self._data_read16(seg, (offset + 2) & 0xffff))
                else:
                    return (pci, self._data_read16(seg, offset))
            else:
                if self._ord_seg is not None:
                    seg = self._ord_seg
                else:
                    seg = self._n_ss
                if double:
                    return (pci, 
                            self._data_read16(seg, (self._bp + offset) & 0xffff),
                            self._data_read16(seg, (self._bp + offset + 2) & 0xffff))
                else:
                    return (pci, 
                            self._data_read16(seg, (self._bp + offset) & 0xffff))
        elif rm == 7:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            if double:
                return (pci, 
                        self._data_read16(seg, (self._bx + offset) & 0xffff),
                        self._data_read16(seg, (self._bx + offset + 2) & 0xffff))
            else:
                return (pci, 
                        self._data_read16(seg, (self._bx + offset) & 0xffff))
        elif rm == 4:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            if double:
                return (pci, 
                        self._data_read16(seg, (self._si + offset) & 0xffff),
                        self._data_read16(seg, (self._si + offset + 2) & 0xffff))
            else:
                return (pci, 
                        self._data_read16(seg, (self._si + offset) & 0xffff))
        elif rm == 5:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            if double:
                return (pci, 
                        self._data_read16(seg, (self._di + offset) & 0xffff),
                        self._data_read16(seg, (self._di + offset + 2) & 0xffff))
            else:
                return (pci, self._data_read16(seg, (self._di + offset) & 0xffff))
        elif rm == 0:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            if double:
                return (pci, 
                        self._data_read16(seg, (self._bx + self._si + offset) & 0xffff),
                        self._data_read16(seg, (self._bx + self._si + offset + 2) & 0xffff))
            else:
                return (pci, self._data_read16(seg, (self._bx + self._si + offset) & 0xffff))
        elif rm == 1:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            if double:
                return (pci, 
                        self._data_read16(seg, (self._bx + self._di + offset) & 0xffff),
                        self._data_read16(seg, (self._bx + self._di + offset + 2) & 0xffff))
            else:
                return (pci, 
                        self._data_read16(seg, (self._bx + self._di + offset) & 0xffff))
        elif rm == 2:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ss
            if double:
                return (pci, 
                        self._data_read16(seg, (self._bp + self._si + offset) & 0xffff),
                        self._data_read16(seg, (self._bp + self._si + offset + 2) & 0xffff))
            else:
                return (pci, 
                        self._data_read16(seg, (self._bp + self._si + offset) & 0xffff))
        else:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ss
            if double:
                return (pci, 
                        self._data_read16(seg, (self._bp + self._di + offset) & 0xffff),
                        self._data_read16(seg, (self._bp + self._di + offset + 2) & 0xffff))
            else:
                return (pci, 
                        self._data_read16(seg, (self._bp + self._di + offset) & 0xffff))

    def _ptr_write16(self, mod, rm, value, scanDisp):
        if mod == 0x00:
            if rm == 6:
                if scanDisp:
                    offset = self._fetch() + (self._fetch() << 8)
                    pci = 2
                else:
                    offset = self._ptr_offset_cache
                    pci = self._ptr_pci_cache
            else:
                offset = 0
                pci = 0
        elif mod == 0x40:
            if scanDisp:
                offset = self._fetch()
                if offset > 0x7f:
                    offset = -((-offset) & 0xff)
                pci = 1
            else:
                offset = self._ptr_offset_cache
                pci = self._ptr_pci_cache
        else:
            if scanDisp:
                offset = self._fetch() + (self._fetch() << 8)
                pci = 2
            else:
                offset = self._ptr_offset_cache
                pci = self._ptr_pci_cache
        self._ord_clear = True
        if rm == 6:
            if mod == 0x00:
                if self._ord_seg is not None:
                    seg = self._ord_seg
                else:
                    seg = self._n_ds
                self._data_write16(seg, offset, value)
            else:
                if self._ord_seg is not None:
                    seg = self._ord_seg
                else:
                    seg = self._n_ss
                self._data_write16(seg, (self._bp + offset) & 0xffff, value)
        elif rm == 7:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            self._data_write16(seg, (self._bx + offset) & 0xffff, value)
        elif rm == 4:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            self._data_write16(seg, (self._si + offset) & 0xffff, value)
        elif rm == 5:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            self._data_write16(seg, (self._di + offset) & 0xffff, value)
        elif rm == 0:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            self._data_write16(seg, (self._bx + self._si + offset) & 0xffff, value)
        elif rm == 1:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            self._data_write16(seg, (self._bx + self._di + offset) & 0xffff, value)
        elif rm == 2:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ss
            self._data_write16(seg, (self._bp + self._si + offset) & 0xffff, value)
        else:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ss
            self._data_write16(seg, (self._bp + self._di + offset) & 0xffff, value)
        return pci

    def _ptr_read8(self, mod, rm):
        if mod == 0x00:
            if rm == 6:
                offset = self._fetch() + (self._fetch() << 8)
                pci = 2
            else:
                offset = 0
                pci = 0
        elif mod == 0x40:
            offset = self._fetch()
            if offset > 0x7f:
                offset = -((-offset) & 0xff)
            pci = 1
        else:
            offset = self._fetch() + (self._fetch() << 8)
            pci = 2
        self._ptr_offset_cache = offset
        self._ptr_pci_cache = pci
        self._ord_clear = True
        if rm == 6:
            if mod == 0x00:
                if self._ord_seg is not None:
                    seg = self._ord_seg
                else:
                    seg = self._n_ds
                return (pci, self._data_read8(seg, offset))
            else:
                if self._ord_seg is not None:
                    seg = self._ord_seg
                else:
                    seg = self._n_ss
                return (pci, 
                        self._data_read8(seg, (self._bp + offset) & 0xffff))
        elif rm == 7:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            return (pci, 
                    self._data_read8(seg, (self._bx + offset) & 0xffff))
        elif rm == 4:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            return (pci, 
                    self._data_read8(seg, (self._si + offset) & 0xffff))
        elif rm == 5:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            return (pci, 
                    self._data_read8(seg, (self._di + offset) & 0xffff))
        elif rm == 0:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            return (pci, 
                    self._data_read8(seg, (self._bx + self._si + offset) & 0xffff))
        elif rm == 1:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            return (pci, 
                    self._data_read8(seg, (self._bx + self._di + offset) & 0xffff))
        elif rm == 2:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ss
            return (pci, 
                    self._data_read8(seg, (self._bp + self._si + offset) & 0xffff))
        else:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ss
            return (pci, 
                    self._data_read8(seg, (self._bp + self._di + offset) & 0xffff))

    def _ptr_write8(self, mod, rm, value, scanDisp):
        if mod == 0x00:
            if rm == 6:
                if scanDisp:
                    offset = self._fetch() + (self._fetch() << 8)
                    pci = 2
                else:
                    offset = self._ptr_offset_cache
                    pci = self._ptr_pci_cache
            else:
                offset = 0
                pci = 0
        elif mod == 0x40:
            if scanDisp:
                offset = self._fetch()
                if offset > 0x7f:
                    offset = -((-offset) & 0xff)
                pci = 1
            else:
                offset = self._ptr_offset_cache
                pci = self._ptr_pci_cache
        else:
            print("ptr8 wr unknown modrm: %02x %02x" % (mod, rm))
            self.hlt = True
            return 0
        self._ord_clear = True
        if rm == 6:
            if mod == 0x00:
                if self._ord_seg is not None:
                    seg = self._ord_seg
                else:
                    seg = self._n_ds
                self._data_write8(seg, offset, value)
            else:
                if self._ord_seg is not None:
                    seg = self._ord_seg
                else:
                    seg = self._n_ss
                self._data_write8(seg, (self._bp + offset) & 0xffff, value)
        elif rm == 7:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            self._data_write8(seg, (self._bx + offset) & 0xffff, value)
        elif rm == 4:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            self._data_write8(seg, (self._si + offset) & 0xffff, value)
        elif rm == 5:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            self._data_write8(seg, (self._di + offset) & 0xffff, value)
        elif rm == 0:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            self._data_write8(seg, (self._bx + self._si + offset) & 0xffff, value)
        elif rm == 1:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ds
            self._data_write8(seg, (self._bx + self._di + offset) & 0xffff, value)
        elif rm == 2:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ss
            self._data_write8(seg, (self._bp + self._si + offset) & 0xffff, value)
        else:
            if self._ord_seg is not None:
                seg = self._ord_seg
            else:
                seg = self._n_ss
            self._data_write8(seg, (self._bp + self._di + offset) & 0xffff, value)
        return pci

    def _set_flags16(self, value):
        f = self._flags
        f.z = value == 0x0000
        f.s = (value & 0x8000) != 0x0000
        n = 0
        m = 0x8000
        for i in self._rng16:
            if value & m:
                n += 1
            m >>= 1
        f.p = (n & 0x1) == 0x0

    def _set_flags8(self, value):
        f = self._flags
        f.z = value == 0x00
        f.s = (value & 0x80) != 0x00
        n = 0
        m = 0x80
        for i in self._rng8:
            if value & m:
                n += 1
            m >>= 1
        f.p = (n & 0x1) == 0x0

    def _get_flags(self):
        f = self._flags
        t = 0x0000
        if f.c:
            t |= 0x0001
        if f.p:
            t |= 0x0004
        if f.a:
            t |= 0x0010
        if f.z:
            t |= 0x0040
        if f.s:
            t |= 0x0080
        if f.i:
            t |= 0x0200
        if f.d:
            t |= 0x0400
        if f.o:
            t |= 0x0800
        return t

    def _put_flags(self, value):
        f = self._flags
        f.c = ((value & 0x0001) != 0x0000)
        f.p = ((value & 0x0004) != 0x0000)
        f.a = ((value & 0x0010) != 0x0000)
        f.z = ((value & 0x0040) != 0x0000)
        f.s = ((value & 0x0080) != 0x0000)
        f.i = ((value & 0x0200) != 0x0000)
        f.d = ((value & 0x0400) != 0x0000)
        f.o = ((value & 0x0800) != 0x0000)

    @property
    def _al(self):
        return self._ax & 0x00ff

    @_al.setter
    def _al(self, value):
        self._ax = (self._ax & 0xff00) | value

    @property
    def _ah(self):
        return self._ax >> 8

    @_ah.setter
    def _ah(self, value):
        self._ax = (self._ax & 0x00ff) | (value << 8)

    @property
    def _bl(self):
        return self._bx & 0x00ff

    @_bl.setter
    def _bl(self, value):
        self._bx = (self._bx & 0xff00) | value

    @property
    def _bh(self):
        return self._bx >> 8

    @_bh.setter
    def _bh(self, value):
        self._bx = (self._bx & 0x00ff) | (value << 8)

    @property
    def _cl(self):
        return self._cx & 0x00ff

    @_cl.setter
    def _cl(self, value):
        self._cx = (self._cx & 0xff00) | value

    @property
    def _ch(self):
        return self._cx >> 8

    @_ch.setter
    def _ch(self, value):
        self._cx = (self._cx & 0x00ff) | (value << 8)

    @property
    def _dl(self):
        return self._dx & 0x00ff

    @_dl.setter
    def _dl(self, value):
        self._dx = (self._dx & 0xff00) | value

    @property
    def _dh(self):
        return self._dx >> 8

    @_dh.setter
    def _dh(self, value):
        self._dx = (self._dx & 0x00ff) | (value << 8)

    def _print_state(self):
        print("AX=%04x BX=%04x CX=%04x DX=%04x SI=%04x DI=%04x" % \
              (self._ax, self._bx, self._cx, self._dx, self._si, self._di))
        print("IP=%04x SP=%04x BP=%04x (PF)=%04x" % \
              (self._ip, self._sp, self._bp, self._pf))
        print("CS=%04x SS=%04x DS=%04x ES=%04x" % \
              (self._cs, self._ss, self._ds, self._es))
        f = self._flags
        print("O=%d D=%d I=%d S=%d Z=%d A=%d P=%d C=%d" % \
              (f.o, f.d, f.i, f.s, f.z, f.a, f.p, f.c))
        print()
        
        
class i8088(i8086):

    def __init__(self, memAs, ioAs, mips = 1.0, clkOut = None):
        i8086.__init__(self, memAs, ioAs, mips, clkOut)
        self._iq = collections.deque(maxlen = 4)
    
    def _data_read16(self, seg, offset):
        addr = (getattr(self, seg) << 4) + offset
        mr = self._mem.read8
        return  mr(addr) + (mr(addr + 1) << 8)
        
    def _data_write16(self, seg, offset, value):
        addr = (getattr(self, seg) << 4) + offset
        mw = self._mem.write8
        mw(addr, value & 0xff)
        mw(addr + 1, value >> 8)
        
    def _fill_iq(self):
        iq = self._iq
        bc = 4 - len(iq)
        if bc >= 1:
            pf = self._pf
            ca = self._cs << 4
            mr = self._mem.read8
            ap = iq.appendleft
            #print("fill %d %04x" % (bc, pf))
            while bc > 0: 
                ap(mr(ca + pf))
                pf = (pf + 1) & 0xffff
                bc -= 1
            self._pf = pf


    


        

