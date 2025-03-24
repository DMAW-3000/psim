
from processor import Processor
import memory


class mc68000(Processor):

    class AddressError(RuntimeError) : pass

    class _Flags(object):

        def __init__(self):
            self.x = False
            self.n = False
            self.v = False
            self.c = False
            self.z = False

            
    def __init__(self, memAs, mips, clkOut, intrLevel, intrAck):
        Processor.__init__(self, mips, clkOut)
        
        self._rng8 = range(8)
        self._rng4 = range(4)
        
        self._intr_level = intrLevel
        self._intr_ack = intrAck
        
        self._flags = self._Flags()
        self._mem = memAs
        
        self._d = [0x00000000] * 8
        self._a = [0x00000000] * 8
        
        self._pc = 0x00000000
        self._ir = 0x0000
        
        self._sr = 0x27
        self._usp = 0x00000000
        self._ssp = 0x00000000
        
        self._exc_addr = 0x00000000
        self._exc_info = 0x0000
        self._exc_stack = []
        self._trace_start = False
        
        self._op_map = [None] * 16
        
        m = self._op_map
        m[0x0] = self._bitm
        m[0x1] = self._move8
        m[0x2] = self._move32
        m[0x3] = self._move16
        m[0x4] = self._cntl
        m[0x5] = self._stcc
        m[0x6] = self._br
        m[0x7] = self._moveq
        m[0x8] = self._or
        m[0x9] = self._sub
        m[0xb] = self._cmpeor
        m[0xc] = self._and
        m[0xd] = self._add
        m[0xe] = self._shift
        
        self._bitm1_map = {
            0x07c : self._orisr,
            0xa3c : self._eoriccr,
        }
        
        self._bitm2_map = {
            0x18 : self._addi,
            0x19 : self._addi,
            0x1a : self._addi,
            0x10 : self._subi,
            0x11 : self._subi,
            0x12 : self._subi,
            0x30 : self._cmpi,
            0x31 : self._cmpi,
            0x32 : self._cmpi,
            0x00 : self._ori,
            0x01 : self._ori,
            0x02 : self._ori,
            0x08 : self._andi,
            0x09 : self._andi,
            0x0a : self._andi,
            0x20 : self._btsti,
            0x04 : self._btstd,
            0x0c : self._btstd,
            0x14 : self._btstd,
            0x1c : self._btstd,
            0x24 : self._btstd,
            0x2c : self._btstd,
            0x34 : self._btstd,
            0x3c : self._btstd,
            0x22 : self._bclri,
            0x23 : self._bseti,
            0x07 : self._bsetd,
            0x0f : self._bsetd,
            0x17 : self._bsetd,
            0x1f : self._bsetd,
            0x27 : self._bsetd,
            0x2f : self._bsetd,
            0x37 : self._bsetd,
            0x3f : self._bsetd,
        }
        
        self._cntl_map1 = {
            0xe71 : self._nop,
            0xe72 : self._stop,
            0xe73 : self._rte,
            0xe75 : self._rts,
            0xe60 : self._moveusp,
            0xe61 : self._moveusp,
            0xe62 : self._moveusp,
            0xe63 : self._moveusp,
            0xe64 : self._moveusp,
            0xe65 : self._moveusp,
            0xe66 : self._moveusp,
            0xe67 : self._moveusp,
            0xe68 : self._moveusp,
            0xe69 : self._moveusp,
            0xe6a : self._moveusp,
            0xe6b : self._moveusp,
            0xe6c : self._moveusp,
            0xe6d : self._moveusp,
            0xe6e : self._moveusp,
            0xe40 : self._trap,
            0xe41 : self._trap,
            0xe42 : self._trap,
            0xe43 : self._trap,
            0xe44 : self._trap,
            0xe45 : self._trap,
            0xe46 : self._trap,
            0xe47 : self._trap,
            0xe48 : self._trap,
            0xe49 : self._trap,
            0xe4a : self._trap,
            0xe4b : self._trap,
            0xe4c : self._trap,
            0xe4d : self._trap,
            0xe4e : self._trap,
            0xe4f : self._trap,
            0x840 : self._swap,
            0x841 : self._swap,
            0x842 : self._swap,
            0x843 : self._swap,
            0x844 : self._swap,
            0x845 : self._swap,
            0x846 : self._swap,
            0x847 : self._swap,
            0xe50 : self._link16,
            0xe51 : self._link16,
            0xe52 : self._link16,
            0xe53 : self._link16,
            0xe54 : self._link16,
            0xe55 : self._link16,
            0xe56 : self._link16,
            0xe57 : self._link16,
            0xe58 : self._unlink,
            0xe59 : self._unlink,
            0xe5a : self._unlink,
            0xe5b : self._unlink,
            0xe5c : self._unlink,
            0xe5d : self._unlink,
            0xe5e : self._unlink,
            0xe5f : self._unlink,
            0xafa : self._illegal,
            0xafb : self._illegal,
            0xafc : self._illegal,
        }
        
        self._cntl_map2 = {
            0x03 : self._movesrrd,
            0x1b : self._movesrwr,
            0x21 : self._pea,
            0x3a : self._jsr,
            0x3b : self._jmp,
            0x28 : self._tst,
            0x29 : self._tst,
            0x2a : self._tst,
            0x08 : self._clr,
            0x09 : self._clr,
            0x0a : self._clr,
            0x18 : self._not,
            0x19 : self._not,
            0x1a : self._not,
            0x10 : self._neg,
            0x11 : self._neg,
            0x12 : self._neg,
            0x07 : self._lea,
            0x0f : self._lea,
            0x17 : self._lea,
            0x1f : self._lea,
            0x27 : self._lea,
            0x2f : self._lea,
            0x37 : self._lea,
            0x3f : self._lea,
            0x22 : self._movem16,
            0x32 : self._movem16,
            0x23 : self._movem32,
            0x33 : self._movem32,
        }
        
    def _reset(self):
        self._sr = 0x27
        self._a[7] = self._mem_read32(0)
        self._pc = self._mem_read32(4)
        self.ivec = 1

    def _check_break(self, blist):
        return self._pc in blist
            
    def _disable_log(self):
        self._mem.disable_trc()
        
    def _enable_log(self):
        self._mem.enable_trc()
       
    def _step(self):
        try:
            op = self._ir = self._mem_read16(self._pc)
            f = self._op_map[op >> 12]
            if f is None:
                print("ERROR: unknown opcode %04x" % op)
                self.halt()
                return
            pci = f(op)
            self._pc = (self._pc + pci) & 0xffffffff
            if self._sr & 0x80:
                if self._trace_start:
                    self._trace_start = False
                else:
                    self._do_trap(0x09)
                    self._sr &= 0x7f
        except (self.AddressError, memory.BusError) as exc:
            if isinstance(exc, self.AddressError):
                vec = 0x03
            else:
                (minfo, maddr) = self._mem.get_error()
                if minfo:
                    self._exc_info |= 0x0010
                else:
                    self._exc_info &= 0xffef
                self._exc_addr = maddr
                vec = 0x02
            self._exc_info &= 0xfff0
            if self._sr & 0x20:
                self._exc_info |= 0x0004
            if len(self._exc_stack):
                pVec = self._exc_stack[-1]
                if not (((pVec >= 0x05) and (pVec >= 0x07)) or \
                       ((pVec >= 0x20) and (pVec <= 0x2f))):
                    self._exc_info |= 0x0008
            print("EXC: %02x %04x %08x" % (vec, self._exc_info, self._exc_addr))
            self._do_trap(vec)
            a = self._a
            sp = a[7]
            self._mem_write16(sp - 8, self._exc_info)
            self._mem_write32(sp - 6, self._exc_addr)
            self._mem_write16(sp - 2, self._ir)
            a[7] = (sp - 8) & 0xffffffff

    def _intr(self):
        level = self._intr_level()
        sr = self._sr
        if level <= (sr & 0x07):
            #print("intr defer", self.ilvl)
            return
        vec = self._intr_ack(level)
        print("intr %d %02x" % (level, vec))
        a = self._a
        if not (sr & 0x20):
            self._usp = a[7]
            sp = self._ssp
        else:
            sp = a[7]
        self._mem_write16(sp - 6, self._get_flags())
        self._mem_write32(sp - 4, self._pc)
        a[7] = (sp - 6) & 0xffffffff
        self._pc = self._mem_read32(vec << 2)
        self._exc_stack.append(vec)
        self._sr = (sr & 0x78) | 0x20 | level
        
    def _move8(self, op):
        (x, spci) = self._ea_read8(op & 0x003f, 2, False)
        spci += 2
        dpci = self._ea_write8((op & 0x0fc0) >> 6, spci, x, True)
        if ((op & 0x01c0) >> 6) != 1:
            self._set_flags8(x)
        return spci + dpci
        
    def _move16(self, op):
        (x, spci) = self._ea_read16(op & 0x003f, 2, False)
        spci += 2
        dpci = self._ea_write16((op & 0x0fc0) >> 6, spci, x, True)
        if ((op & 0x01c0) >> 6) != 1:
            self._set_flags16(x)
        return spci + dpci
        
    def _move32(self, op):
        (x, spci) = self._ea_read32(op & 0x003f, 2, False)
        spci += 2
        dpci = self._ea_write32((op & 0x0fc0) >> 6, spci, x, True)  
        if ((op & 0x01c0) >> 6) != 1:
            self._set_flags32(x)
        return spci + dpci
        
    def _add(self, op):
        mode1 = (op & 0x003f) >> 3
        mode2 = (op & 0x01c0) >> 6
        if (op & 0x0100) and (mode2 != 7) and ((mode1 == 0) or (mode1 == 1)):
            return self._addx(op)
        modreg = op & 0x003f
        reg = (op & 0x0e00) >> 9
        d = self._d
        a = self._a
        f = self._flags
        if mode2 == 0:
            (x, pci) = self._ea_read8(modreg, 2, False)
            t = (d[reg] & 0x000000ff) + x
            f.c = f.x = (t > 0xff)
            t &= 0xff
            d[reg] = t | (d[reg] & 0xffffff00)
            self._set_flags8(t)
        elif (mode2 == 1) or (mode2 == 5):
            (x, pci) = self._ea_read16(modreg, 2, False)
            t = (d[reg] & 0x0000ffff) + x
            f.c = f.x = (t > 0xffff)
            t &= 0xffff
            if mode2 == 1:
                d[reg] = t | (d[reg] & 0xffff0000)
            else:
                self._ea_write16(modreg, 2, t, False)
            self._set_flags16(t)
        elif (mode2 == 2) or (mode2 == 6):
            (x, pci) = self._ea_read32(modreg, 2, False)
            t = d[reg] + x
            f.c = f.x = (t > 0xffffffff)
            t &= 0xffffffff
            if mode2 == 2:
                d[reg] = t
            else:
                self._ea_write32(modreg, 2, t, False)
            self._set_flags32(t)
        elif mode2 == 7:
            (x, pci) = self._ea_read32(modreg, 2, False)
            t = a[reg] + x
            a[reg] = t & 0xffffffff
        else:
            print("ERROR: unknown add mode %d" % mode2)
            self.halt()
            return 0
        return pci + 2
        
    def _addx(self, op):
        regy = op & 0x0007
        size = (op & 0x00c0) >> 6
        regx = (op & 0x0e00) >> 9
        d = self._d
        f = self._flags
        if size == 2:
            if op & 0x0008:
                a = self._a
                a[regy] = addr = (a[regy] - 4) & 0xffffffff
                y = self._mem_read32(addr)
            else:
                y = d[regy]
            t = d[regx] + y + int(f.x)
            f.c = f.x = (t > 0xffffffff)
            t &= 0xffffffff
            d[regx] = t
            self._set_flags32(t)
        else:
            print("ERROR: unsupported addx size %d" % size)
            self.halt()
            return 0
        return 2
        
    def _sub(self, op):
        modreg = op & 0x003f
        mode = (op & 0x01c0) >> 6
        reg = (op & 0x0e00) >> 9
        d = self._d
        a = self._a
        f = self._flags
        if mode == 0:
            (x, pci) = self._ea_read8(modreg, 2, False)
            t = (d[reg] & 0x000000ff) - x
            f.c = f.x = (t < 0)
            t &= 0xff
            d[reg] = (d[reg] & 0xffffff00) | t
            self._set_flags8(t)
        elif mode == 2:
            (x, pci) = self._ea_read32(modreg, 2, False)
            t = d[reg] - x
            f.c = f.x = (t < 0)
            t &= 0xffffffff
            d[reg] = t
            self._set_flags32(t)
        elif mode == 7:
            (x, pci) = self._ea_read32(modreg, 2, False)
            t = a[reg] - x
            a[reg] = t & 0xffffffff
        else:
            print("ERROR: unknown sub mode %d" % mode)
            self.halt()
            return 0
        return pci + 2
        
    def _cmpeor(self, op):
        modreg = op & 0x003f
        mode = (op & 0x01c0) >> 6
        reg = (op & 0x0e00) >> 9
        f = self._flags
        if (mode == 0):
            (y, pci) = self._ea_read8(modreg, 2, False)
            t = (self._d[reg] & 0x000000ff) - y
            f.c = (t < 0)
            self._set_flags8(t & 0xff)
        elif (mode == 1):
            (y, pci) = self._ea_read16(modreg, 2, False)
            t = (self._d[reg] & 0x0000ffff) - y
            f.c = (t < 0)
            self._set_flags16(t & 0xffff)
        elif (mode == 2) or (mode == 7):
            (y, pci) = self._ea_read32(modreg, 2, False)
            if mode == 7:
                t = self._a[reg] - y
            else:
                t = self._d[reg] - y
            f.c = (t < 0)
            self._set_flags32(t & 0xffffffff)
        elif (mode == 3):
            (y, pci) = self._ea_read16(modreg, 2, False)
            if y & 0x8000:
                y |= 0xffff0000
            t = self._a[reg] - y
            f.c = (t < 0)
            self._set_flags32(t & 0xffffffff)
        elif (mode == 4):
            (y, pci) = self._ea_read8(modreg, 2, False)
            t = (self._d[reg] & 0x000000ff) ^ y
            self._ea_write8(modreg, 2, t, False)
            f.c = f.v = False
            self._set_flags8(t)
        elif (mode == 6):
            (y, pci) = self._ea_read32(modreg, 2, False)
            t = self._d[reg] ^ y
            self._ea_write32(modreg, 2, t, False)
            f.c = f.v = False
            self._set_flags32(t)
        else:
            print("ERROR: unknown cmpeor mode %d" % mode)
            self.halt()
            return 0
        return pci + 2
        
    def _and(self, op):
        opmode = (op & 0x01f8) >> 3
        if (opmode == 0x28) or (opmode == 0x29) or (opmode == 0x31):
            return self._exg(op)
        modreg = op & 0x003f
        mode = (op & 0x01c0) >> 6
        reg = (op & 0x0e00) >> 9
        d = self._d
        f = self._flags
        if (mode == 0):
            (y, pci) = self._ea_read8(modreg, 2, False)
            t = (d[reg] & 0x000000ff) & y
            d[reg] = (d[reg] & 0xffffff00) | t
            self._set_flags8(t)
        elif (mode == 1):
            (y, pci) = self._ea_read16(modreg, 2, False)
            t = (d[reg] & 0x0000ffff) & y
            d[reg] = (d[reg] & 0xffff0000) | t
            self._set_flags16(t)
        elif (mode == 2):
            (y, pci) = self._ea_read32(modreg, 2, False)
            d[reg] = t = d[reg] & y
            self._set_flags32(t)
        elif (mode == 3):               # mulu.w
            (y, pci) = self._ea_read16(op & 0x003f, 2, False)
            t = (d[reg] & 0x0000ffff) * y
            f.v = (t > 0xffffffff)
            t &= 0xffffffff
            d[reg] = t  
            self._set_flags32(t)
        else:
            print("ERROR: unknown and mode %d" % mode)
            self.halt()
            return 0
        f.c = False
        if mode != 3:
            f.v = False
        return pci + 2
        
    def _or(self, op):
        modreg = op & 0x003f
        mode = (op & 0x01c0) >> 6
        reg = (op & 0x0e00) >> 9
        d = self._d
        f = self._flags
        if (mode == 0):
            (y, pci) = self._ea_read8(modreg, 2, False)
            t = (d[reg] & 0x000000ff) | y
            d[reg] = (d[reg] & 0xffffff00) | t
            self._set_flags8(t)
        elif (mode == 1):
            (y, pci) = self._ea_read16(modreg, 2, False)
            t = (d[reg] & 0x0000ffff) | y
            d[reg] = (d[reg] & 0xffff0000) | t
            self._set_flags16(t)
        elif mode == 3:                 # divu.w
            (y, pci) = self._ea_read16(modreg, 2, False)
            q = d[reg] // y
            r = d[reg] % y
            f.v = of = q > 0xffff
            if not of:
                d[reg] = (r << 16) | q
                self._set_flags16(q)
        else:
            print("ERROR: unknown or mode %d" % mode)
            self.halt()
            return 0
        f.c = False
        if mode != 3:
            f.v = False
        return pci + 2
        
    def _exg(self, op):
        opmode = (op & 0x00f8) >> 3
        regx = (op & 0x0e00) >> 9
        regy = op & 0x0007
        a = self._a
        d = self._d
        if opmode == 0x08:
            t = d[regx]
            d[regx] = d[regy]
            d[regy] = t
        elif opmode == 0x11:
            t = d[regx]
            d[regx] = a[regy]
            a[regy] = t
        else:
            print("ERROR: unsupported exg mode %02x" % opmode)
            self.halt()
            return 0
        return 2
        
    def _bitm(self, op):
        code = op & 0x0fff
        try:
            f = self._bitm1_map[code]
            return f(op)
        except KeyError:
            pass
        sub = (code & 0x0fc0) >> 6
        mode = (code & 0x0038) >> 3
        if mode == 0x1:
            pci = self._movep(op)
        else:
            try:
                f = self._bitm2_map[sub]
                pci = f(op)
            except KeyError:
               print("ERROR: unknown bitm sub mode %04x %02x" % (op, sub))
               self.halt()
               return 0
        return pci
        
    def _addi(self, op):
        modrm = op & 0x003f
        size = (op & 0x00c0) >> 6
        f = self._flags
        if size == 0:
            (x, pci) = self._ea_read8(modrm, 4, False)
            t = x + (self._mem_read16(self._pc + 2) & 0x00ff)
            f.c = f.x = (t > 0xff)
            t &= 0xff
            self._ea_write8(modrm, 4, t, False)
            self._set_flags8(t)
            pci += 2
        elif size == 2:
            (x, pci) = self._ea_read32(modrm, 6, False)
            t = x + self._mem_read32(self._pc + 2)
            f.c = f.x = (t > 0xffffffff)
            t &= 0xffffffff
            self._ea_write32(modrm, 6, t, False)
            self._set_flags32(t)
            pci += 4
        else:
            print("ERROR: unknown addi size %d" % size)
            self.halt()
            return 0
        return pci + 2
        
    def _subi(self, op):
        modrm = op & 0x003f
        size = (op & 0x00c0) >> 6
        f = self._flags
        if size == 2:
            (x, pci) = self._ea_read32(modrm, 6, False)
            t = x - self._mem_read32(self._pc + 2)
            f.c = f.x = (t < 0)
            t &= 0xffffffff
            self._ea_write32(modrm, 6, t, False)
            self._set_flags32(t)
            pci += 4
        else:
            print("ERROR: unknown addi size %d" % size)
            self.halt()
            return 0
        return pci + 2
        
    def _cmpi(self, op):
        modrm = op & 0x003f
        size = (op & 0x00c0) >> 6
        f = self._flags
        if size == 0:
            (x, pci) = self._ea_read8(modrm, 4, False)
            t = x - (self._mem_read16(self._pc + 2) & 0x00ff)
            f.c = (t < 0)
            self._set_flags8(t & 0xff)
            pci += 2
        elif size == 1:
            (x, pci) = self._ea_read16(modrm, 4, False)
            t = x - self._mem_read16(self._pc + 2)
            f.c = (t < 0)
            self._set_flags16(t & 0xffff)
            pci += 2
        elif size == 2:
            (x, pci) = self._ea_read32(modrm, 4, False)
            t = x - self._mem_read32(self._pc + 2)
            f.c = (t < 0)
            self._set_flags32(t & 0xffffffff)
            pci += 4
        else:
            print("ERROR: unsupported cmpi size %d" % size)
            self.halt()
            return 0
        return pci + 2
        
    def _ori(self, op):
        modrm = op & 0x003f
        size = (op & 0x00c0) >> 6
        f = self._flags
        if size == 1:
            (x, pci) = self._ea_read16(modrm, 4, False)
            t = x | self._mem_read16(self._pc + 2)
            self._ea_write16(modrm, 4, t, False)
            self._set_flags16(t)
            pci += 2
        else:
            print("ERROR: unsupported ori size %d" % size)
            self.halt()
            return 0
        f.c = f.v = False
        return pci + 2
        
    def _andi(self, op):
        modrm = op & 0x003f
        size = (op & 0x00c0) >> 6
        f = self._flags
        if size == 1:
            (x, pci) = self._ea_read16(modrm, 4, False)
            t = x & self._mem_read16(self._pc + 2)
            self._ea_write16(modrm, 4, t, False)
            self._set_flags16(t)
            pci += 2
        else:
            print("ERROR: unsupported andi size %d" % size)
            self.halt()
            return 0
        f.v = f.c = False
        return pci + 2
        
    def _btsti(self, op):
        mode = (op & 0x0038) >> 3
        b = self._mem_read16(self._pc + 2) & 0x001f 
        if mode == 0:
            (x, pci) = self._ea_read32(op & 0x003f, 4, False)
        else:
            (x, pci) = self._ea_read8(op & 0x003f, 4, False)
        self._flags.z = (x & (0x00000001 << b)) == 0x00000000
        return pci + 4
        
    def _btstd(self, op):
        mode = (op & 0x0038) >> 3
        reg = (op & 0x0e00) >> 9
        m = 0x00000001 << (self._d[reg] & 0x0000001f)
        if mode == 0:
            (x, pci) = self._ea_read32(op & 0x003f, 2, False)
        else:
            (x, pci) = self._ea_read8(op & 0x003f, 2, False)
        self._flags.z = (m & x) == 0x00000000
        return pci + 2
        
    def _bclri(self, op):
        modreg = (op & 0x003f)
        mode = (op & 0x0038) >> 3
        b = self._mem_read16(self._pc + 2) & 0x001f
        m = 0x00000001 << b
        if mode == 0:
            (x, pci) = self._ea_read32(modreg, 4, False)
        else:
            (x, pci) = self._ea_read8(modreg, 4, False)
        self._flags.z = (x & m) == 0x00000000
        x &= (~m)
        if mode == 0:
            self._ea_write32(modreg, 4, x, False)
        else:
            self._ea_write8(modreg, 4, x, False)
        return pci + 4
        
    def _bseti(self, op):
        modreg = (op & 0x003f)
        mode = (op & 0x0038) >> 3
        m = 0x00000001 << (self._mem_read16(self._pc + 2) & 0x001f)
        if mode == 0:
            (x, pci) = self._ea_read32(modreg, 4, False)
        else:
            (x, pci) = self._ea_read8(modreg, 4, False)
        self._flags.z = (x & m) == 0x00000000
        x |= m
        if mode == 0:
            self._ea_write32(modreg, 4, x, False)
        else:
            self._ea_write8(modreg, 4, x, False)
        return pci + 4
        
    def _bsetd(self, op):
        modreg = (op & 0x003f)
        mode = (op & 0x0038) >> 3
        reg = (op & 0x0e00) >> 9
        m = 0x00000001 << (self._d[reg] & 0x0000001f)
        if mode == 0:
            (x, pci) = self._ea_read32(modreg, 2, False)
        else:
            (x, pci) = self._ea_read8(modreg, 2, False)
        self._flags.z = (m & x) == 0x00000000
        x |= m
        if mode == 0:
            self._ea_write32(modreg, 4, x, False)
        else:
            self._ea_write8(modreg, 4, x, False)
        return pci + 2
        
    def _movep(self, op):
        dreg = (op & 0x0e00) >> 9
        mode = (op & 0x01c0) >> 6
        areg = op & 0x0007
        disp = self._mem_read16(self._pc + 2)
        if disp & 0x8000:
            disp |= 0xffff0000
        addr = (self._a[areg] + disp) & 0xffffffff
        if mode == 5:
            x = 0x00000000
            for n in self._rng4:
                x |= self._mem_read8(addr) << ((3 - n) * 8)
                addr = (addr + 2) & 0xffffffff
            self._d[dreg] = x
        elif mode == 7:
            m = 0xff000000
            x = self._d[dreg]
            for n in self._rng4:
                self._mem_write8(addr, (x & m) >> ((3 - n) * 8))
                m >>= 8
                addr = (addr + 2) & 0xffffffff
        else:
            print("ERROR: movep unsupported mode %d" % mode)
            self.halt()
            return 0
        return 4
        
    def _shift(self, op):
        mode = (op & 0x0018) >> 3
        if mode == 0:
            pci = self._ash(op)
        elif mode == 1:
            pci = self._lsh(op)
        elif mode == 2:
            pci = self._rox(op)
        elif mode == 3:
            pci = self._ro(op)
        else:
            print("ERROR: unknown shift mode %d" % mode)
            self.halt()
            return 0
        return pci
    
    def _lsh(self, op):
        d = self._d
        f = self._flags
        right = ((op & 0x0100) == 0x0000)
        size = (op & 0x00c0) >> 6
        count = (op & 0x0e00) >> 9
        if op & 0x0020:
            count = d[count] & 0x0000003f
        else:
            if count == 0:
                count = 8
        reg = op & 0x0007
        if size == 0:
            for c in range(count):
                t = d[reg] & 0x000000ff
                if right:
                    f.c = f.x = ((t & 0x01) != 0x00)
                    t >>= 1
                else:
                    f.c = f.x = ((t & 0x80) != 0x00)
                    t <<= 1
                d[reg] = (d[reg] & 0xffffff00) | (t & 0xff)
            self._set_flags8(t & 0xff)
        elif size == 1:
            for c in range(count):
                t = d[reg] & 0x0000ffff
                if right:
                    f.c = f.x = ((t & 0x0001) != 0x0000)
                    t >>= 1
                else:
                    f.c = f.x = ((t & 0x8000) != 0x0000)
                    t <<= 1
                d[reg] = (d[reg] & 0xffff0000) | (t & 0xffff)
            self._set_flags16(t & 0xffff)
        elif size == 2:
            for c in range(count):
                t = d[reg]
                if right:
                    f.c = f.x = ((t & 0x00000001) != 0x0000000)
                    t >>= 1
                else:
                    f.c = f.x = ((t & 0x80000000) != 0x0000000)
                    t <<= 1
                d[reg] = t & 0xffffffff
            self._set_flags32(t & 0xffffffff)
        else:
            print("ERROR: unsupported lsh size %d" % size)
            self.halt()
            return 0
        f.v = False
        return 2
        
    def _ash(self, op):
        d = self._d
        f = self._flags
        right = ((op & 0x0100) == 0x0000)
        size = (op & 0x00c0) >> 6
        count = (op & 0x0e00) >> 9
        if op & 0x0020:
            count = d[count] & 0x0000003f
        else:
            if count == 0:
                count = 8
        reg = op & 0x0007
        if size == 0:
            sign = ((d[reg] & 0x00000080) != 0x00000000)
            for c in range(count):
                t = d[reg] & 0x000000ff
                if right:
                    f.c = f.x = ((t & 0x01) != 0x00)
                    t >>= 1
                    if sign:
                        t |= 0x80
                else:
                    f.c = f.x = ((t & 0x80) != 0x00)
                    t <<= 1
                d[reg] = (d[reg] & 0xffffff00) | (t & 0xff)
            self._set_flags8(t & 0xff)
        elif size == 1:
            sign = ((d[reg] & 0x00008000) != 0x00000000)
            for c in range(count):
                t = d[reg] & 0x0000ffff
                if right:
                    f.c = f.x = ((t & 0x0001) != 0x0000)
                    t >>= 1
                    if sign:
                        t |= 0x8000
                else:
                    f.c = f.x = ((t & 0x8000) != 0x0000)
                    t <<= 1
                d[reg] = (d[reg] & 0xffff0000) | (t & 0xffff)
            self._set_flags16(t & 0xffff)
        elif size == 2:
            sign = ((d[reg] & 0x80000000) != 0x00000000)
            for c in range(count):
                t = d[reg]
                if right:
                    f.c = f.x = ((t & 0x00000001) != 0x00000000)
                    t >>= 1
                    if sign:
                        t |= 0x80000000
                else:
                    f.c = f.x = ((t & 0x80000000) != 0x00000000)
                    t <<= 1
                d[reg] = t & 0xffffffff
            self._set_flags32(t & 0xffffffff)
        else:
            print("ERROR: unsupported ash size %d" % size)
            self.halt()
            return 0
        f.v = False
        return 2
        
    def _ro(self, op):
        d = self._d
        f = self._flags
        right = ((op & 0x0100) == 0x0000)
        size = (op & 0x00c0) >> 6
        count = (op & 0x0e00) >> 9
        if op & 0x0020:
            count = d[count] & 0x0000003f
        else:
            if count == 0:
                count = 8
        reg = op & 0x0007
        if size == 1:
            for c in range(count):
                t = d[reg] & 0x0000ffff
                if right:
                    f.c = ((t & 0x0001) != 0x0000)
                    t >>= 1
                    if f.c:
                        t |= 0x8000
                else:
                    f.c = ((t & 0x8000) != 0x0000)
                    t <<= 1
                    if f.c:
                        t |= 0x0001
                d[reg] = (d[reg] & 0xffff0000) | (t & 0xffff)
            self._set_flags16(t & 0xffff)
        elif size == 2:
            for c in range(count):
                t = d[reg]
                if right:
                    f.c = ((t & 0x00000001) != 0x00000000)
                    t >>= 1
                    if f.c:
                        t |= 0x80000000
                else:
                    f.c = ((t & 0x80000000) != 0x00000000)
                    t <<= 1
                    if f.c:
                        t |= 0x00000001
                d[reg] = t & 0xffffffff
            self._set_flags32(t & 0xffffffff)
        else:
            print("ERROR: unsupported ro size %d" % size)
            self.halt()
            return 0
        f.v = False
        return 2
        
    def _rox(self, op):
        d = self._d
        f = self._flags
        right = (op & 0x0100) == 0x0000
        size = (op & 0x00c0) >> 6
        count = (op & 0x0e00) >> 9
        if op & 0x0020:
            count = d[count] & 0x0000003f
        else:
            if count == 0:
                count = 8
        reg = op & 0x0007
        if size == 0:
            for c in range(count):
                t = d[reg] & 0x000000ff
                xsave = f.x
                if right:
                    f.c = f.x = ((t & 0x01) != 0x00)
                    t >>= 1
                    if xsave:
                        t |= 0x80
                else:
                    f.c = f.x = ((t & 0x80) != 0x00)
                    t <<= 1
                    if xsave:
                        t |= 0x01
                d[reg] = (d[reg] & 0xffffff00) | (t & 0xff)
            self._set_flags8(t & 0xff)
        elif size == 1:
            for c in range(count):
                t = d[reg] & 0x0000ffff
                xsave = f.x
                if right:
                    f.c = f.x = ((t & 0x0001) != 0x0000)
                    t >>= 1
                    if xsave:
                        t |= 0x8000
                else:
                    f.c = f.x = ((t & 0x8000) != 0x0000)
                    t <<= 1
                    if xsave:
                        t |= 0x0001
                d[reg] = (d[reg] & 0xffff0000) | (t & 0xffff)
            self._set_flags16(t & 0xffff)
        else:
            print("ERROR: unsupported rox size %d" % size)
            self.halt()
            return 0
        f.v = False
        return 2
        
    def _stcc(self, op):
        size = (op & 0x00c0) >> 6
        if size != 3:
            if op & 0x0100:
                return self._subq(op)
            else:
                return self._addq(op)
        opmode = (op & 0x00f8) >> 3
        if opmode == 0x19:
            pci = self._dbcc(op)
        else:
            print("ERROR: unknown stcc opmode %02x" % opmode)
            self.halt()
            return 0
        return pci
        
    def _addq(self, op):
        modrm = op & 0x003f
        mode = (op & 0x0038) >> 3
        size = (op & 0x00c0) >> 6
        y = (op & 0x0e00) >> 9
        f = self._flags
        if size == 0:
            (x, pci) = self._ea_read8(modrm, 2, False)
            t = x + y
            if mode != 1:
                f.c = f.x = (t > 0xff)
            t &= 0xff
            self._ea_write8(modrm, 2, t, False)
            if mode != 1:
                self._set_flags8(t)
        elif size == 1:
            (x, pci) = self._ea_read16(modrm, 2, False)
            t = x + y
            if mode != 1:
                f.c = f.x = (t > 0xffff)
            t &= 0xffff
            self._ea_write16(modrm, 2, t, False)
            if mode != 1:
                self._set_flags16(t)
        elif size == 2:
            (x, pci) = self._ea_read32(modrm, 2, False)
            t = x + y
            if mode != 1:
                f.c = f.x = (t > 0xffffffff)
            t &= 0xffffffff
            self._ea_write32(modrm, 2, t, False)
            if mode != 1:
                self._set_flags32(t)
        else:
            print("ERROR: unsupported addq size %d" % size)
            self.halt()
            return 0
        return pci + 2
        
    def _subq(self, op):
        modrm = op & 0x003f
        mode = (op & 0x0038) >> 3
        size = (op & 0x00c0) >> 6
        y = (op & 0x0e00) >> 9
        f = self._flags
        if size == 1:
            (x, pci) = self._ea_read16(modrm, 2, False)
            t = x - y
            if mode != 1:
                f.c = f.x = (t < 0)
            t &= 0xffff
            self._ea_write16(modrm, 2, t, False)
            if mode != 1:
                self._set_flags16(t)
        elif size == 2:
            (x, pci) = self._ea_read32(modrm, 2, False)
            t = x - y
            if mode != 1:
                f.c = f.x = (t < 0)
            t &= 0xffffffff
            self._ea_write32(modrm, 2, t, False)
            if mode != 1:
                self._set_flags32(t)
        else:
            print("ERROR: unsupported subq size %d" % size)
            self.halt()
            return 0
        return pci + 2
        
    def _dbcc(self, op):
        cond = (op & 0x0f00) >> 8
        reg = op & 0x0007
        d = self._d
        pci = 4
        if (cond == 1) or (not self._check_cond(cond)):
            t = (d[reg] & 0x0000ffff) - 1
            d[reg] = (d[reg] & 0xffff0000) | (t & 0xffff)
            if t >= 0:
                disp = self._mem_read16(self._pc + 2)
                if disp & 0x8000:
                    disp |= 0xffff0000
                self._pc = (self._pc + 2 + disp) & 0xffffffff
                pci = 0
        return pci
            
    def _br(self, op):
        cond = (op & 0x0f00) >> 8
        disp = op & 0x00ff
        if disp == 0x00:
            disp = self._mem_read16(self._pc + 2)
            if disp & 0x8000:
                disp |= 0xffff0000
            dispSize = 2
        elif disp == 0xff:
            print("ERROR: br unsupported disp")
            self.halt()
            return 0
        else:
            if disp & 0x80:
                disp += 0xffffff00
            dispSize = 0
        if self._check_cond(cond):
            if cond == 1:
                a = (self._a[7] - 4) & 0xffffffff
                self._a[7] = a
                self._mem_write32(a, (self._pc + 2 + dispSize) & 0xffffffff)
            self._pc = (self._pc + 2 + disp) & 0xffffffff
            pci = 0
        else:
            pci = dispSize + 2
        return pci
        
    def _check_cond(self, cond):
        f = self._flags
        if (cond == 0) or (cond == 1):
            return True
        elif cond == 6:
            return (not f.z)
        elif cond == 7:
            return f.z
        elif cond == 5:
            return f.c
        elif cond == 4:
            return (not f.c)
        elif cond == 11:
            return f.n
        elif cond == 8:
            return (not f.v)
        elif cond == 9:
            return f.v
        elif cond == 10:
            return (not f.n)
        elif cond == 2:
            return (not f.c) and (not f.z)
        elif cond == 3:
            return f.c or f.z
        elif cond == 12:
            return (f.n and f.v) or ((not f.n) and (not f.v))
        elif cond == 13:
            return (f.n and (not f.v)) or ((not f.n) and f.v)
        elif cond == 15:
            return f.z or (f.n and (not f.v)) or ((not f.n) and f.v)
        elif cond == 14:
            return (f.n and f.v and (not f.z)) or ((not f.n) and (not f.v) and (not f.z))
        else:
            print("ERROR: br unsupported cond %d" % cond)
            self.halt()
            return False
            
    def _moveq(self, op):
        if op & 0x0100:
            print("ERROR: unknown moveq op %04x" % op)
            self.halt()
            return 0
        f = self._flags
        x = op & 0x00ff
        if x & 0x80:
            x |= 0xffffff00
        self._d[(op & 0x0e00) >> 9] = x
        f.c = f.c = False
        self._set_flags32(x)
        return 2
        
    def _cntl(self, op):
        code = op & 0x0fff
        try:
            f = self._cntl_map1[code]
            return f(op)
        except KeyError:
           pass
        sub = (code & 0x0fc0) >> 6
        try:
            f = self._cntl_map2[sub]
        except KeyError:
            print("ERROR: unknown ctl sub mode %04x %02x" % (op, sub))
            self.halt()
            return 0
        return f(op)
        
    def _nop(self, op):
        return 2
        
    def _stop(self, op):
        self.halt()
        return 0
        
    def _illegal(self, op):
        self._do_trap(0x04)
        return 0
        
    def _jsr(self, op):
        mode = (op & 0x0038) >> 3
        reg = op & 0x0007
        a = self._a
        addr = (a[7] - 4) & 0xffffffff
        a[7] = addr
        self._mem_write32(addr, (self._pc + 2) & 0xffffffff)
        if mode == 2:
            self._pc = a[reg]
        else:
            print("ERROR: unsupported jsr mode %d" % mode)
            self.halt()
            return 0
        return 0
        
    def _jmp(self, op):
        mode = (op & 0x0038) >> 3
        reg = op & 0x0007
        a = self._a
        if mode == 2:
            self._pc = a[reg]
        elif mode == 7:
            if reg == 0:
                self._pc = self._mem_read16(self._pc + 2)
            else:
                print("ERROR: unsupported jmp mode %d %d" % (mode, reg))
                self.halt()
                return 0
        else:
            print("ERROR: unsupported jmp mode %d" % mode)
            self.halt()
            return 0
        return 0
        
    def _rts(self, op):
        a = self._a
        addr = a[7]
        self._pc = self._mem_read32(addr)
        a[7] = (addr + 4) & 0xffffffff
        return 0
        
    def _rte(self, op):
        a = self._a
        sp = a[7]
        self._put_flags(self._mem_read16(sp))
        self._pc = self._mem_read32(sp + 2)
        sp = (sp + 6) & 0xffffffff
        sr = self._sr
        if not (sr & 0x20):
            self._ssp = sp
            a[7] = self._usp
        else:
            a[7] = sp
        if sr & 0x80:
            self._trace_start = True
        try:
            self._exc_stack.pop()
        except IndexError:
            pass
        return 0
        
    def _clr(self, op):
        modreg = op & 0x003f
        size = (op & 0x00c0) >> 6
        if size == 0:
            pci = self._ea_write8(modreg, 2, 0, False)
        elif size == 1:
            pci = self._ea_write16(modreg, 2, 0, False)
        elif size == 2:
            pci = self._ea_write32(modreg, 2, 0, False)
        else:
            print("ERROR: clr unsupported size %d" % size)
            self.halt()
            return 0
        f = self._flags
        f.z = True
        f.n = False
        return pci + 2
        
    def _tst(self, op):
        size = (op & 0x00c0) >> 6
        modreg = op & 0x003f
        if size == 0:
            (x, pci) = self._ea_read8(modreg, 2, False)
            self._set_flags8(x)
        elif size == 1:
            (x, pci) = self._ea_read16(modreg, 2, False)
            self._set_flags16(x)
        elif size == 2:
            (x, pci) = self._ea_read32(modreg, 2, False)
            self._set_flags32(x)
        else:
            print("ERROR: tst unknown size %d" % size)
            self.halt()
            return 0
        f = self._flags
        f.v = f.c = False
        return pci + 2
        
    def _not(self, op):
        size = (op & 0x00c0) >> 6
        modreg = op & 0x003f
        if size == 0:
            (x, pci) = self._ea_read8(modreg, 2, False)
            x = (~x) & 0xff
            self._ea_write8(modreg, 2, x, False)
            self._set_flags8(x)
        elif size == 1:
            (x, pci) = self._ea_read16(modreg, 2, False)
            x = (~x) & 0xffff
            self._ea_write16(modreg, 2, x, False)
            self._set_flags16(x)
        elif size == 2:
            (x, pci) = self._ea_read32(modreg, 2, False)
            x = (~x) & 0xffffffff
            self._ea_write32(modreg, 2, x, False)
            self._set_flags32(x)
        else:
            print("ERROR: not unknown size %d" % size)
            self.halt()
            return 0
        f = self._flags
        f.v = f.c = False
        return pci + 2
        
    def _neg(self, op):
        size = (op & 0x00c0) >> 6
        modreg = op & 0x003f
        if size == 2:
            (x, pci) = self._ea_read32(modreg, 2, False)
            x = (0 - x) & 0xffffffff
            self._ea_write32(modreg, 2, x, False)
            self._set_flags32(x)
        else:
            print("ERROR: neg unknown size %d" % size)
            self.halt()
            return 0
        f = self._flags
        f.c = f.x = (not f.z)
        return pci + 2
        
    def _movesrrd(self, op):
        pci = self._ea_write16(op & 0x003f, 2, self._get_flags(), False)
        return pci + 2
        
    def _movesrwr(self, op):
        (x, pci) = self._ea_read16(op & 0x003f, 2, False)
        self._put_flags(x)
        if self._sr & 0x80:
            self._trace_start = True
        return pci + 2
        
    def _orisr(self, op):
        self._put_flags(self._get_flags() | self._mem_read16(self._pc + 2))
        if self._sr & 0x80:
            self._trace_start = True
        return 4
        
    def _eoriccr(self, op):
        f = self._get_flags()
        x = (f & 0x00ff) ^ (self._mem_read16(self._pc + 2) & 0x00ff)
        self._put_flags((f & 0xff00) | (x & 0x00ff))
        return 4
        
    def _moveusp(self, op):
        if op & 0x0008:
            self._a[op & 0x0007] = self._usp
        else:
            self._usp = self._a[op & 0x0007]
        return 2
        
    def _trap(self, op):
        self._do_trap((op & 0x000f) + 32)
        return 0
        
    def _do_trap(self, vec):
        a = self._a
        sr = self._sr
        if not (sr & 0x20):
            self._usp = a[7]
            sp = self._ssp
        else:
            sp = a[7]
        self._mem_write16(sp - 6, self._get_flags())
        self._mem_write32(sp - 4, self._pc)
        a[7] = (sp - 6) & 0xffffffff
        self._pc = self._mem_read32(vec << 2)
        self._exc_stack.append(vec)
        self._sr = sr | 0x20
        
    def _swap(self, op):
        reg = op & 0x0007
        d = self._d
        t = d[reg] & 0x0000ffff
        d[reg] >>= 16
        d[reg] |= (t << 16)
        return 2
        
    def _ext(self, op):
        mode = (op & 0x01c0) >> 6
        reg = op & 0x0007
        d = self._d
        if mode == 2:
            x = d[reg] & 0x000000ff
            if x & 0x80:
                x |= 0xff00
            d[reg] = (d[reg] & 0xffff0000) | x
        elif mode == 3:
            x = d[reg] & 0x0000ffff
            if x & 0x8000:
                x |= 0xffff0000
            d[reg] = x
        else:
            print("ERROR: unknown ext mode %d" % mode)
            self.halt()
            return 0
        return 2
        
    def _link16(self, op):
        reg = op & 0x0007
        a = self._a
        disp = self._mem_read16(self._pc + 2)
        if disp & 0x8000:
            disp |= 0xffff0000
        addr = (a[7] - 4) & 0xffffffff
        self._mem_write32(addr, a[reg])
        a[reg] = addr
        a[7] = (addr + disp) & 0xffffffff
        return 4
        
    def _unlink(self, op):
        reg = op & 0x0007
        a = self._a
        addr = a[reg]
        a[reg] = self._mem_read32(addr)
        a[7] = (addr + 4) & 0xffffffff
        return 2
        
    def _movem16(self, op):
        mode = (op & 0x0038) >> 3
        reg = (op & 0x0007)
        rmask = self._mem_read16(self._pc + 2)
        d = self._d
        a = self._a
        if (mode == 3) or (mode == 4):
            addr = a[reg]
            pci = 0
        elif mode == 7:
            if reg == 0:
                addr = self._mem_read16(self._pc + 4)
                pci = 2
            else:
                print("ERROR: movem16 unknown reg %d %d" % (mode, reg))
                self.halt()
                return 0
        elif mode == 0:
            return self._ext(op)
        else:
            print("ERROR: movem16 unknown mode %d %d" % (mode, reg))
            self.halt()
            return 0
        m = 0x0001
        if op & 0x0400:
            for n in self._rng8:
                if m & rmask:
                    if mode == 4:
                        addr = (addr - 2) & 0xffffffff
                        t = self._mem_read16(addr)
                        if t & 0x8000:
                            t |= 0xffff0000
                        a[7-n] = t
                        a[reg] = addr
                    else:
                        t = self._mem_read16(addr)
                        if t & 0x8000:
                            t |= 0xffff0000
                        d[n] = t
                        addr = (addr + 2) & 0xffffffff
                        if mode == 3:
                            a[reg] = addr
                m <<= 1
            for n in self._rng8:
                if m & rmask: 
                    if mode == 4:
                        addr = (addr - 2) & 0xffffffff
                        t = self._mem_read16(addr)
                        if t & 0x8000:
                            t |= 0xffff0000
                        d[7-n] = t
                        a[reg] = addr
                    else:
                        t = self._mem_read16(addr)
                        if t & 0x8000:
                            t |= 0xffff0000
                        a[n] = t
                        addr = (addr + 2) & 0xffffffff
                        if mode == 3:
                            a[reg] = addr
                m <<= 1
        else:
            for n in self._rng8:
                if m & rmask:
                    if mode == 4:
                        addr = (addr - 2) & 0xffffffff
                        self._mem_write16(addr, a[7-n] & 0x0000ffff)
                        a[reg] = addr
                    else:
                        self._mem_write16(addr, d[n] & 0x0000ffff)
                        addr = (addr + 2) & 0xffffffff
                        if mode == 3:
                            a[reg] = addr
                m <<= 1
            for n in self._rng8:
                if m & rmask:
                    if mode == 4:
                        addr = (addr - 2) & 0xffffffff
                        self._mem_write16(addr, d[7-n] & 0x0000ffff)
                        a[reg] = addr
                    else:
                        self._mem_write16(addr, a[n] & 0x0000ffff)
                        addr = (addr + 2) & 0xffffffff
                        if mode == 3:
                            a[reg] = addr
                m <<= 1
        return pci + 4
        
    def _movem32(self, op):
        mode = (op & 0x0038) >> 3
        reg = (op & 0x0007)
        rmask = self._mem_read16(self._pc + 2)
        d = self._d
        a = self._a
        if (mode == 2) or (mode == 3) or (mode == 4):
            addr = a[reg]
            pci = 0
        elif mode == 5:
            disp = self._mem_read16(self._pc + 4)
            if disp & 0x8000:
                disp |= 0xffff0000
            addr = (a[reg] + disp) & 0xffffffff
            pci = 2
        elif mode == 0:
            return self._ext(op)
        else:
            print("ERROR: movem32 unknown mode %d %d" % (mode, reg))
            self.halt()
            return 0
        m = 0x0001
        if (op & 0x0400) != 0x0000:
            for n in self._rng8:
                if (m & rmask) != 0x0000:
                    if mode == 4:
                        addr = (addr - 4) & 0xffffffff
                        a[7-n] = self._mem_read32(addr)
                        a[reg] = addr
                    else:
                        d[n] = self._mem_read32(addr)
                        addr = (addr + 4) & 0xffffffff
                        if mode == 3:
                            a[reg] = addr
                m <<= 1
            for n in self._rng8:
                if (m & rmask) != 0x0000: 
                    if mode == 4:
                        addr = (addr - 4) & 0xffffffff
                        d[7-n] = self._mem_read32(addr)
                        a[reg] = addr
                    else:
                        a[n] = self._mem_read32(addr)
                        addr = (addr + 4) & 0xffffffff
                        if mode == 3:
                            a[reg] = addr
                m <<= 1
        else:
            for n in self._rng8:
                if (m & rmask) != 0x0000:
                    if mode == 4:
                        addr = (addr - 4) & 0xffffffff
                        self._mem_write32(addr, a[7-n])
                        a[reg] = addr
                    else:
                        self._mem_write32(addr, d[n])
                        addr = (addr + 4) & 0xffffffff
                        if mode == 3:
                            a[reg] = addr
                m <<= 1
            for n in self._rng8:
                if (m & rmask) != 0x0000:
                    if mode == 4:
                        addr = (addr - 4) & 0xffffffff
                        self._mem_write32(addr, d[7-n])
                        a[reg] = addr
                    else:
                        self._mem_write32(addr, a[n])
                        addr = (addr + 4) & 0xffffffff
                        if mode == 3:
                            a[reg] = addr
                m <<= 1
        return pci + 4
            
        
    def _lea(self, op):
        mode = (op & 0x0038) >> 3
        sreg = op & 0x0007
        dreg = (op & 0x0e00) >> 9
        a = self._a
        if mode == 2:
            a[dreg] = a[sreg]
            pci = 0
        elif mode == 5:
            t = self._mem_read16(self._pc + 2)
            if t & 0x8000:
                t |= 0xffff0000
            a[dreg] = (a[sreg] + t) & 0xffffffff
            pci = 2
        elif mode == 6:
            ext = self._mem_read16(self._pc + 2)
            disp = ext & 0x00ff
            if disp & 0x80:
                disp |= 0xffffff00
            ireg = (ext & 0x7000) >> 12
            if not (ext & 0x8000):
                idx = self._d[ireg]
            else:
                idx = a[ireg]
            a[dreg] = (a[sreg] + disp + idx) & 0xffffffff
            pci = 2
        elif mode == 7:
            if sreg == 0:
                a[dreg] = self._mem_read16(self._pc + 2) 
                pci = 2
            elif sreg == 1:
                a[dreg] = self._mem_read32(self._pc + 2)
                pci = 4
            elif sreg == 2:
                t = self._mem_read16(self._pc + 2)
                if t & 0x8000:
                    t |= 0xffff0000
                a[dreg] = (t + self._pc + 2) & 0xffffffff
                pci = 2
            else:
                print("ERROR: unsupported LEA mode %d %d %d" % (mode, sreg, dreg))
                self.halt()
                return 0
        else:
            print("ERROR: unsupported LEA mode %d %d %d" % (mode, sreg, dreg))
            self.halt()
            return 0
        return pci + 2
        
    def _pea(self, op):
        mode = (op & 0x0038) >> 3
        reg = op & 0x0007
        a = self._a
        if mode == 7:
            if reg == 2:
                t = self._mem_read16(self._pc + 2)
                if t & 0x8000:
                    t |= 0xffff0000
                x = (t + self._pc + 2) & 0xffffffff
                pci = 2
            else:
                print("ERROR: unsupported PEA mode %d %d" % (mode, reg))
                self.halt()
                return 0
        else:
            print("ERROR: unsupported PEA mode %d %d" % (mode, reg))
            self.halt()
            return 0
        addr = (a[7] - 4) & 0xffffffff
        self._mem_write32(addr, x)
        a[7] = addr
        return pci + 2

    def _ea_read8(self, modreg, offset, reverse):
        if not reverse:
            mode = (modreg & 0x38) >> 3
            reg = modreg & 0x07
        else:
            reg = (modreg & 0x38) >> 3
            mode = modreg & 0x07
        if mode == 0:
            value = self._d[reg] & 0x000000ff
            pci = 0
        elif (mode == 2) or (mode == 3) or (mode == 4):
            a = self._a
            if mode == 4:
                if reg == 7:
                    a[reg] = (a[reg] - 2) & 0xffffffff
                else:
                    a[reg] = (a[reg] - 1) & 0xffffffff
            value = self._mem_read8(a[reg])
            if mode == 3:
                if reg == 7:
                    a[reg] = (a[reg] + 2) & 0xffffffff
                else:
                    a[reg] = (a[reg] + 1) & 0xffffffff
            pci = 0
        elif mode == 5:
            disp = self._mem_read16(self._pc + offset)
            if disp & 0x8000:
                disp |= 0xffff0000
            value = self._mem_read8((self._a[reg] + disp) & 0xffffffff)
            pci = 2
        elif mode == 7:
            if reg == 0:
                value = self._mem_read8(self._mem_read16(self._pc + offset))
                pci = 2
            elif reg == 1:
                value = self._mem_read8(self._mem_read32(self._pc + offset))
                pci = 4
            elif reg == 4:
                value = self._mem_read16(self._pc + offset) & 0x00ff
                pci = 2
            else:
                print("ERROR: EA8 rd mode %d %d not supported" % (mode, reg))
                self.halt()
                return (0,0)
        elif mode == 6:
            ext = self._mem_read16(self._pc + offset)
            disp = ext & 0x00ff
            if disp & 0x80:
                disp |= 0xffffff00
            ireg = (ext & 0x7000) >> 12
            if not (ext & 0x8000):
                idx = self._d[ireg]
            else:
                idx = self._a[ireg]
            value = self._mem_read8((self._a[reg] + disp + idx) & 0xffffffff)
            pci = 2
        else:
            print("ERROR: EA8 rd mode %d %d not supported" % (mode, reg))
            self.halt()
            return (0,0)
        return (value, pci)
        
    def _ea_write8(self, modreg, offset, value, reverse):
        if not reverse:
            mode = (modreg & 0x38) >> 3
            reg = modreg & 0x07
        else:
            reg = (modreg & 0x38) >> 3
            mode = modreg & 0x07
        if mode == 0:
            self._d[reg] = (self._d[reg] & 0xffffff00) | value
            pci = 0
        elif (mode == 2) or (mode == 3) or (mode == 4):
            a = self._a
            if mode == 4:
                if reg == 7:
                    a[reg] = (a[reg] - 2) & 0xffffffff
                else:
                    a[reg] = (a[reg] - 1) & 0xffffffff
            self._mem_write8(a[reg], value)
            if mode == 3:
                if reg == 7:
                    a[reg] = (a[reg] + 2) & 0xffffffff
                else:
                    a[reg] = (a[reg] + 1) & 0xffffffff
            pci = 0
        elif mode == 5:
            disp = self._mem_read16(self._pc + offset)
            if disp & 0x8000:
                disp |= 0xffff0000
            self._mem_write8((self._a[reg] + disp) & 0xffffffff, value)
            pci = 2
        elif mode == 7:
            if reg == 0:
                self._mem_write8(self._mem_read16(self._pc + offset), value)
                pci = 2
            elif reg == 1:
                self._mem_write8(self._mem_read32(self._pc + offset), value)
                pci = 4
            else:
                print("ERROR: EA8 wr mode %d %d not supported" % (mode, reg))
                self.halt()
                return 0
        elif mode == 6:
            ext = self._mem_read16(self._pc + offset)
            disp = ext & 0x00ff
            if disp & 0x80:
                disp |= 0xffffff00
            ireg = (ext & 0x7000) >> 12
            if not (ext & 0x8000):
                idx = self._d[ireg]
            else:
                idx = self._a[ireg]
            self._mem_write8((self._a[reg] + disp + idx) & 0xffffffff, value)
            pci = 2
        else:
            print("ERROR: EA8 wr mode %d %d not supported" % (mode, reg))
            self.halt()
            return 0
        return pci
        
    def _ea_read16(self, modreg, offset, reverse):
        if not reverse:
            mode = (modreg & 0x38) >> 3
            reg = modreg & 0x07
        else:
            reg = (modreg & 0x38) >> 3
            mode = modreg & 0x07
        if mode == 0:
            value = self._d[reg] & 0xffff
            pci = 0
        elif (mode == 2) or (mode == 3) or (mode == 4):
            a = self._a
            if mode == 4:
                a[reg] = (a[reg] - 2) & 0xffffffff
            value = self._mem_read16(a[reg])
            if mode == 3:
                a[reg] = (a[reg] + 2) & 0xffffffff
            pci = 0
        elif mode == 5:
            disp = self._mem_read16(self._pc + offset)
            if disp & 0x8000:
                disp |= 0xffff0000
            value = self._mem_read16((self._a[reg] + disp) & 0xffffffff)
            pci = 2
        elif mode == 7:
            if reg == 0:
                value = self._mem_read16(self._mem_read16(self._pc + offset))
                pci = 2
            elif reg == 4:
                value = self._mem_read16(self._pc + offset)
                pci = 2
            elif reg == 3:
                ext = self._mem_read16(self._pc + offset)
                disp = ext & 0x00ff
                if disp & 0x80:
                    disp |= 0xffffff00
                ireg = (ext & 0x7000) >> 12
                if not (ext & 0x8000):
                    idx = self._d[ireg]
                else:
                    idx = self._a[ireg]
                value = self._mem_read16((self._pc + offset + disp + idx) & 0xffffffff)
                pci = 2
            else:
                print("ERROR: EA16 rd mode %d %d not supported" % (mode, reg))
                self.halt()
                return (0, 0)
        elif mode == 6:
            ext = self._mem_read16(self._pc + offset)
            disp = ext & 0x00ff
            if disp & 0x80:
                disp |= 0xffffff00
            ireg = (ext & 0x7000) >> 12
            if not (ext & 0x8000):
                idx = self._d[ireg]
            else:
                idx = self._a[ireg]
            value = self._mem_read16((self._a[reg] + disp + idx) & 0xffffffff)
            pci = 2
        elif mode == 1:
            value = self._a[reg] & 0xffff
            pci = 0
        else:
            print("ERROR: EA16 rd mode %d %d not supported" % (mode, reg))
            self.halt()
            return (0, 0)
        return (value, pci)
        
    def _ea_write16(self, modreg, offset, value, reverse):
        if not reverse:
            mode = (modreg & 0x38) >> 3
            reg = modreg & 0x07
        else:
            reg = (modreg & 0x38) >> 3
            mode = modreg & 0x07
        if mode == 0:
            d = self._d
            d[reg] = (d[reg] & 0xffff0000) | value
            pci = 0
        elif (mode == 2) or (mode == 3) or (mode == 4):
            a = self._a
            if mode == 4:
                a[reg] = (a[reg] - 2) & 0xffffffff
            self._mem_write16(a[reg], value)
            if mode == 3:
                a[reg] = (a[reg] + 2) & 0xffffffff
            pci = 0
        elif mode == 5:
            disp = self._mem_read16(self._pc + offset)
            if disp & 0x8000:
                disp |= 0xffff0000
            self._mem_write16((self._a[reg] + disp) & 0xffffffff, value)
            pci = 2
        elif mode == 7:
            if reg == 0:
                self._mem_write16(self._mem_read16(self._pc + offset), value)
                pci = 2
            else:
                print("ERROR: EA16 wr reg %d %d not supported" % (mode, reg))
                self.halt()
                return 0
        elif mode == 6:
            ext = self._mem_read16(self._pc + offset)
            disp = ext & 0x00ff
            if disp & 0x80:
                disp |= 0xffffff00
            ireg = (ext & 0x7000) >> 12
            if not (ext & 0x8000):
                idx = self._d[ireg]
            else:
                idx = self._a[ireg]
            self._mem_write16((self._a[reg] + disp + idx) & 0xffffffff, value)
            pci = 2
        elif mode == 1:
            if value & 0x8000:
                value |= 0xffff0000
            self._a[reg] = value
            pci = 0
        else:
            print("ERROR: EA16 wr mode %d %d not supported" % (mode, reg))
            self.halt()
            return 0
        return pci
        
    def _ea_read32(self, modreg, offset, reverse):
        if not reverse:
            mode = (modreg & 0x38) >> 3
            reg = modreg & 0x07
        else:
            reg = (modreg & 0x38) >> 3
            mode = modreg & 0x07
        if mode == 0:
            value = self._d[reg]
            pci = 0
        elif mode == 1:
            value = self._a[reg]
            pci = 0
        elif (mode == 2) or (mode == 3):
            a = self._a
            value = self._mem_read32(a[reg])
            if mode == 3:
                a[reg] = (a[reg] + 4) & 0xffffffff
            pci = 0
        elif mode == 5:
            disp = self._mem_read16(self._pc + offset)
            if disp & 0x8000:
                disp |= 0xffff0000
            value = self._mem_read32((self._a[reg] + disp) & 0xffffffff)
            pci = 2
        elif mode == 7:
            if reg == 0:
                value = self._mem_read32(self._mem_read16(self._pc + offset))
                pci = 2
            elif reg == 4:
                value = self._mem_read32(self._pc + offset)
                pci = 4
            else:
                print("ERROR: EA32 rd mode %d %d not supported" % (mode, reg))
                self.halt()
                return (0,0)
        elif mode == 6:
            ext = self._mem_read16(self._pc + offset)
            disp = ext & 0x00ff
            if disp & 0x80:
                disp |= 0xffffff00
            ireg = (ext & 0x7000) >> 12
            if not (ext & 0x8000):
                idx = self._d[ireg]
            else:
                idx = self._a[ireg]
            value = self._mem_read32((self._a[reg] + disp + idx) & 0xffffffff)
            pci = 2
        else:
            print("ERROR: EA32 rd mode %d %d not supported" % (mode, reg))
            self.halt()
            return (0,0)
        return (value, pci)
        
    def _ea_write32(self, modreg, offset, value, reverse):
        if not reverse:
            mode = (modreg & 0x38) >> 3
            reg = modreg & 0x07
        else:
            reg = (modreg & 0x38) >> 3
            mode = modreg & 0x07
        if mode == 0:
            self._d[reg] = value
            pci = 0
        elif mode == 1:
            self._a[reg] = value
            pci = 0
        elif (mode == 2) or (mode == 3) or (mode == 4):
            a = self._a
            if mode == 4:
                a[reg] = (a[reg] - 4) & 0xffffffff
            self._mem_write32(a[reg], value)
            if mode == 3:
                a[reg] = (a[reg] + 4) & 0xffffffff
            pci = 0
        elif mode == 5:
            disp = self._mem_read16(self._pc + offset)
            if disp & 0x8000:
                disp |= 0xffff0000
            self._mem_write32((self._a[reg] + disp) & 0xffffffff, value)
            pci = 2
        elif mode == 7:
            if reg == 0:
                self._mem_write32(self._mem_read16(self._pc + offset), value)
                pci = 2
            else:
                print("ERROR: EA16 wr reg %d %d not supported" % (mode, reg))
                self.halt()
                return 0
        elif mode == 6:
            ext = self._mem_read16(self._pc + offset)
            disp = ext & 0x00ff
            if disp & 0x80:
                disp |= 0xffffff00
            ireg = (ext & 0x7000) >> 12
            if not (ext & 0x8000):
                idx = self._d[ireg]
            else:
                idx = self._a[ireg]
            self._mem_write32((self._a[reg] + disp + idx) & 0xffffffff, value)
            pci = 2
        else:
            print("ERROR: EA32 wr mode %d %d not supported" % (mode, reg))
            self.halt()
            return 0
        return pci
        
    def _mem_read8(self, addr):
        return self._mem.read8(addr & 0x00ffffff)
        
    def _mem_write8(self, addr, value):
        self._mem.write8(addr & 0x00ffffff, value)
        
    def _mem_read16(self, addr):
        if addr & 0x00000001:
            self._exc_addr = addr
            self._exc_info |= 0x0010
            raise self.AddressError
        return self._mem.read16be(addr & 0x00ffffff)
        
    def _mem_write16(self, addr, value):
        if addr & 0x00000001:
            self._exc_addr = addr
            self._exc_info &= 0xffef
            raise self.AddressError
        self._mem.write16be(addr & 0x00ffffff, value)
        
    def _mem_read32(self, addr):
        if addr & 0x00000001:
            self._exc_addr = addr
            self._exc_info |= 0x0010
            raise self.AddressError
        addr &= 0x00ffffff
        mr = self._mem.read16be
        return (mr(addr) << 16) + mr(addr + 2) 
        
    def _mem_write32(self, addr, value):
        if addr & 0x00000001:
            self._exc_addr = addr
            self._exc_info &= 0xffef
            raise self.AddressError
        addr &= 0x00ffffff
        mw = self._mem.write16be
        mw(addr, value >> 16)
        mw(addr + 2, value & 0xffff)       
        
    def _set_flags8(self, value):
        f = self._flags
        f.z = value == 0x00
        f.n = (value & 0x80) != 0x00
        
    def _set_flags16(self, value):
        f = self._flags
        f.z = value == 0x0000
        f.n = (value & 0x8000) != 0x0000
        
    def _set_flags32(self, value):
        f = self._flags
        f.z = value == 0x00000000
        f.n = (value & 0x80000000) != 0x00000000
        
    def _get_flags(self):
        f = self._flags
        x = 0x00
        if f.c:
            x |= 0x01
        if f.v:
            x |= 0x02
        if f.z:
            x |= 0x04
        if f.n:
            x |= 0x08
        if f.x:
            x |= 0x10
        return (self._sr << 8) | x
        
    def _put_flags(self, value):
        self._sr = value >> 8
        f = self._flags
        f.c = (value & 0x0001) != 0x0000
        f.v = (value & 0x0002) != 0x0000
        f.z = (value & 0x0004) != 0x0000
        f.n = (value & 0x0008) != 0x0000
        f.x = (value & 0x0010) != 0x0000
        
    def _print_state(self):
        for n in self._rng8:
            print("D%d=%08x A%d=%08x" % (n, self._d[n], n, self._a[n]))
        print("PC=%08x SR=%02x" % (self._pc, self._sr))
        print("(USP)=%08x (SSP)=%08x" % (self._usp, self._ssp))
        print("X=%d N=%d V=%d Z=%d C=%d" % \
              (self._flags.x, self._flags.n, self._flags.v, self._flags.z, self._flags.c))
        print()