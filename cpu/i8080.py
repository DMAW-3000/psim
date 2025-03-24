                    
from processor import *

class i8080(Processor):
    """
    Intel 8080 processor
    """

    class _Flags(object):
        """
        8080 flags
        """
        def __init__(self):
            self.z = False
            self.s = False
            self.p = False
            self.cy = False
            self.ac = False
            

    def __init__(self, memAs, ioAs, clkMod = 4, clkOut = None):
        Processor.__init__(self, clkMod, clkOut)
        
        self._flags = self._Flags()
        self._mem = memAs
        self._io = ioAs
        self._iv = None
        self._ie = False
        self._intr_pc = False

        self._mr = memAs.read8
        self._mw = memAs.write8
        
        self._rng8 = range(8)
        
        self._a = 0x00
        self._b = 0x00
        self._c = 0x00
        self._d = 0x00
        self._e = 0x00
        self._h = 0x00
        self._l = 0x00
        
        self._pc = 0x0000
        self._sp = 0x0000

        self._reg_map = ("_b", "_c", "_d", "_e", "_h", "_l", "_m", "_a")

        self._arith_map = {
            0x10 : self._ADD,
            0x11 : self._ADC,
            0x12 : self._SUB,
            0x13 : self._SBB,                    
            0x14 : self._ANA,
            0x15 : self._XRA,
            0x16 : self._ORA,
            0x17 : self._CMP,
        }

        self._ldst_map = {
            0x3a : self._LDA,
            0x32 : self._STA,
            0x17 : self._RAL,
            0x07 : self._RLC,
            0x1f : self._RAR,
            0x0f : self._RRC,
            0x2f : self._CMA,
            0x2a : self._LHLD,
            0x22 : self._SHLD,
            0x27 : self._DAA,
            0x37 : self._STC,
            0x3f : self._CMC,
            0x00 : self._NOP,
            0x10 : self._NOP,
        }

        self._default_ldst_map = [None] * 16
        m = self._default_ldst_map
        m[0x01] = self._LXI
        m[0x06] = self._MVI
        m[0x0e] = self._MVI
        m[0x04] = self._INR
        m[0x0c] = self._INR
        m[0x05] = self._DCR
        m[0x0d] = self._DCR
        m[0x03] = self._INX
        m[0x0b] = self._DCX
        m[0x0a] = self._LDAX
        m[0x02] = self._STAX
        m[0x09] = self._DAD

        self._cntl_map = {
            0xc3 : self._JMP,
            0xcd : self._CALL,
            0xc9 : self._RET,
            0xc6 : self._ADI,
            0xce : self._ACI,
            0xd6 : self._SUI,
            0xde : self._SBI,
            0xfe : self._CPI,
            0xdb : self._IN,
            0xd3 : self._OUT,
            0xe6 : self._ANI,
            0xf6 : self._ORI,
            0xee : self._XRI,
            0xe9 : self._PCHL,
            0xeb : self._XCHG,
            0xe3 : self._XTHL,
            0xf5 : self._PUSHPSW,
            0xf1 : self._POPPSW,
            0xf9 : self._SPHL,
            0xfb : self._EI,
            0xf3 : self._DI,
        }

        self._default_cntl_map = [None] * 16
        m = self._default_cntl_map
        m[0x05] = self._PUSH
        m[0x01] = self._POP
        m[0x02] = self._Jc
        m[0x0a] = self._Jc
        m[0x04] = self._Cc
        m[0x0c] = self._Cc
        m[0x00] = self._Rc
        m[0x08] = self._Rc
        m[0x07] = self._RST
        m[0x0f] = self._RST

    @property
    def _m(self):
        return self._mr((self._h << 8) + self._l)

    @_m.setter
    def _m(self, value):
        self._mw((self._h << 8) + self._l, value)
        
    def _disable_log(self):
        self._mem.disable_trc()
        self._io.disable_trc()
        
    def _enable_log(self):
        self._mem.enable_trc()
        self._io.enable_trc()
        
    def _reset(self):
        self._pc = 0x0000
        self._iv = None
        self._ie = False
        self._intr_pc = False

    def _intr(self):
        if not self._ie:
            #print("int deferred")
            return
        print("int %02x" % self.ivec)
        self._iv = self.ivec
        self._intr_pc = True
        self.ivec = None

    def _step(self):
        pc = self._pc
        if self._iv is not None:
            op = self._iv
            self._iv = None
            self._ie = False
        else:
            op = self._mr(pc)
        t = op & 0xc0
        if t == 0x40:
            ddd = (op & 0x38) >> 3
            sss = op & 0x07
            if (ddd == 6) and (sss == 6):
                self.halt()
                return
            self._reg_write(ddd, self._reg_read(sss))
            self._pc = pc + 1
        elif t == 0x00:
            f = self._ldst_map.get(op, self._default_ldst)
            self._pc = f(op, pc) + pc
        elif t == 0x80: 
            try:
                f = self._arith_map[(op & 0xf8) >> 3]
            except KeyError:
                print("ERROR: unknown opcode: %02x" % op)
                self.halt()
                return
            f(op & 0x07)
            self._pc = pc + 1
        else:
            f = self._cntl_map.get(op, self._default_cntl)
            f(op, pc)

    def _check_break(self, blist):
        return self._pc in blist

    def _LDA(self, op, pc):
        mr = self._mr
        self._a = mr(mr(pc + 1) + (mr(pc + 2) << 8))
        return 3
        
    def _STA(self, op, pc):
        mr = self._mr
        self._mw(mr(pc + 1) + (mr(pc + 2) << 8), self._a)
        return 3
        
    def _RAL(self, op, pc):
        f = self._flags
        t = self._a << 1
        if f.cy:
            t |= 0x01
        f.cy = ((t & 0x100) != 0x0000)
        self._a = t & 0xff
        return 1
        
    def _RAR(self, op, pc):
        a = self._a
        f = self._flags
        t = a & 0x01
        a >>= 1
        if f.cy:
            a |= 0x80
        self._a = a
        f.cy = (t != 0x00)
        return 1
        
    def _RRC(self, op, pc):
        a = self._a
        f = self._flags
        t = a & 0x01
        a >>= 1
        if t != 0x00:
            f.cy = True
            a |= 0x80
        else:
            f.cy = False
        self._a = a
        return 1

    def _RLC(self, op, pc):
        a = self._a
        f = self._flags
        t = a & 0x80
        a = (a << 1) & 0xff
        if t != 0x00:
            f.cy = True
            a |= 0x01
        else:
            f.cy = False
        self._a = a
        return 1
        
    def _CMA(self, op, pc):
        self._a = (~self._a) & 0xff
        return 1

    def _LHLD(self, op, pc):
        mr = self._mr
        a0 = mr(pc + 1) + (mr(pc + 2) << 8)
        self._l = mr(a0)
        self._h = mr(a0 + 1)
        return 3
        
    def _SHLD(self, op, pc):
        mr = self._mr
        mw = self._mw
        a0 = mr(pc + 1) + (mr(pc + 2) << 8)
        mw(a0, self._l)
        mw(a0 + 1, self._h)
        return 3

    def _DAA(self, op, pc):
        f = self._flags
        x = self._a
        if ((x & 0x0f) > 9) or f.ac:
            x += 0x06
        t = (x & 0xf0) >> 4
        if (t > 9) or f.cy:
            x += 0x60
        f.cy = (x > 255)
        x &= 0xff
        self._a = x
        self._set_flags(x)
        return 1
        
    def _STC(self, op, pc):
        self._flags.cy = True
        return 1

    def _CMC(self, op, pc):
        self._flags.cy = not self._flags.cy
        return 1

    def _NOP(self, op, pc):
        return 1

    def _default_ldst(self, op, pc):
        f = self._default_ldst_map[op & 0x0f]
        if f is None:
            print("ERROR: unknown opocde: %02x" % op)
            self.halt()
            return 0
        return f(op, pc)
            
    def _LXI(self, op, pc):
        mr = self._mr
        self._rp_write((op & 0x30) >> 4, mr(pc + 1), mr(pc + 2))
        return 3
    
    def _MVI(self, op, pc):
        self._reg_write((op & 0x38) >> 3, self._mr(pc + 1))
        return 2
    
    def _INR(self, op, pc):
        ddd = (op & 0x38) >> 3
        x = self._reg_read(ddd)
        t = (x + 1) & 0xff
        self._reg_write(ddd, t)
        self._flags.ac = (((x & 0x0f) + 1) > 0x0f)
        self._set_flags(t)
        return 1
    
    def _DCR(self, op, pc):
        ddd = (op & 0x38) >> 3
        x = self._reg_read(ddd)
        t = (x - 1) & 0xff
        self._reg_write(ddd, t)
        self._flags.ac = (((x & 0x0f) + 1) > 0x0f)
        self._set_flags(t)
        return 1
    
    def _INX(self, op, pc):
        self._rp_incr((op & 0x30) >> 4)
        return 1
            
    def _DCX(self, op, pc): 
        self._rp_decr((op & 0x30) >> 4)
        return 1
            
    def _LDAX(self, op, pc): 
        (a0, a1) = self._rp_read((op & 0x30) >> 4)
        self._a = self._mr((a1 << 8) + a0)
        return 1
    
    def _STAX(self, op, pc):
        (a0, a1) = self._rp_read((op & 0x30) >> 4)
        self._mw((a1 << 8) + a0, self._a)
        return 1
    
    def _DAD(self, op, pc): 
        (x0, x1) = self._rp_read((op & 0x30) >> 4)
        d0 = (self._h << 8) + self._l + (x1 << 8) + x0
        self._flags.cy = (d0 > 0xffff)
        self._h = (d0 >> 8) & 0xff
        self._l = d0 & 0xff
        return 1

    def _ADD(self, sss):
        f = self._flags
        x = self._a
        y = self._reg_read(sss)
        x0 = x + y  
        f.cy = (x0 > 255)
        f.ac = (((x & 0x0f) + (y & 0x0f)) > 0x0f)
        x0 &= 0xff
        self._a = x0
        self._set_flags(x0)

    def _ADC(self, sss):
        f = self._flags
        x = self._a
        y = self._reg_read(sss)
        c = int(f.cy)
        x0 = x + y + c
        f.cy = (x0 > 255)
        f.ac = (((x & 0x0f) + (y & 0x0f) + c) > 0x0f)
        x0 &= 0xff
        self._a = x0
        self._set_flags(x0)

    def _SUB(self, sss):
        f = self._flags
        x = self._a
        y = self._reg_read(sss)
        x0 = x - y 
        f.cy = (x0 < 0)
        f.ac = (((x & 0x0f) - (y & 0x0f)) < 0)
        x0 &= 0xff
        self._a = x0
        self._set_flags(x0)

    def _SBB(self, sss):
        f = self._flags
        x = self._a
        y = self._reg_read(sss)
        c = int(f.cy)
        x0 = x - y - c
        f.cy = (x0 < 0)
        f.ac = (((x & 0x0f) - (y & 0x0f) - c) < 0)
        x0 &= 0xff
        self._a = x0 
        self._set_flags(x0)

    def _ORA(self, sss):
        self._a = t = self._a | self._reg_read(sss)
        self._flags.cy = False
        self._set_flags(t)
        
    def _ANA(self, sss):
        self._a = t = self._a & self._reg_read(sss)
        self._flags.cy = False
        self._set_flags(t)

    def _XRA(self, sss):
        self._a = t = self._a ^ self._reg_read(sss)
        self._flags.cy = False
        self._set_flags(t)
        
    def _CMP(self, sss):
        f = self._flags
        x = self._a
        y = self._reg_read(sss)
        t = x - y
        f.cy = (t < 0)
        f.ac = (((x & 0x0f) - (y & 0x0f)) < 0)
        self._set_flags(t & 0xff)

    def _JMP(self, op, pc):
        mr = self._mr
        self._pc = mr(pc + 1) + (mr(pc + 2) << 8)
        
    def _CALL(self, op, pc):
        an = (pc + 3) & 0xffff
        sp = self._sp
        mw = self._mw
        mr = self._mr
        pc = mr(pc + 1) + (mr(pc + 2) << 8)
        mw(sp - 1, an >> 8)
        mw(sp - 2, an & 0xff)
        self._sp = (sp - 2) & 0xffff 
        self._pc = pc

    def _RET(self, op, pc):
        sp = self._sp
        mr = self._mr
        self._pc = mr(sp) + (mr(sp + 1) << 8)
        self._sp = (sp + 2) & 0xffff
        
    def _ADI(self, op, pc):
        f = self._flags
        x = self._a
        y = self._mr(pc + 1)
        t = x + y 
        f.cy = (t > 255)
        f.ac = (((x & 0x0f) + (y & 0x0f)) > 0x0f)
        t &= 0xff
        self._a = t
        self._set_flags(t)
        self._pc = pc + 2

    def _ACI(self, op, pc):
        f = self._flags
        x = self._a
        y = self._mr(pc + 1)
        c = int(f.cy)
        t = x + y + c
        f.cy = (t > 255)
        f.ac = (((x & 0x0f) + (y & 0x0f) + c) > 0x0f)
        t &= 0xff
        self._a = t
        self._set_flags(t)
        self._pc = pc + 2

    def _SUI(self, op, pc):
        f = self._flags
        x = self._a
        y = self._mr(pc + 1)
        t = x - y
        f.cy = (t < 0)
        f.ac = (((x & 0x0f) - (y & 0x0f)) < 0)
        t &= 0xff
        self._a = t
        self._set_flags(t)
        self._pc = pc + 2

    def _SBI(self, op, pc):
        f = self._flags
        x = self._a
        y = self._mr(pc + 1)
        c = int(f.cy)
        t = x - y - c
        f.cy = (t < 0)
        f.ac = (((x & 0x0f) - (y & 0x0f) - c) < 0)
        t &= 0xff
        self._a = t
        self._set_flags(t)
        self._pc = pc + 2

    def _CPI(self, op, pc):
        f = self._flags
        x = self._a
        y = self._mr(pc + 1)
        t = x - y
        f.cy = (t < 0)
        f.ac = (((x & 0x0f) - (y & 0x0f)) < 0)
        self._set_flags(t & 0xff)
        self._pc = pc + 2

    def _IN(self, op, pc): 
        self._a = self._io.read8(self._mr(pc + 1))
        self._pc = pc + 2

    def _OUT(self, op, pc):
        self._io.write8(self._mr(pc + 1), self._a)
        self._pc = pc + 2

    def _ANI(self, op, pc): 
        self._a = t = self._a & self._mr(pc + 1)
        self._flags.cy = False
        self._set_flags(t)
        self._pc = pc + 2

    def _ORI(self, op, pc):
        self._a = t = self._a | self._mr(pc + 1)
        self._flags.cy = False
        self._set_flags(t)
        self._pc = pc + 2

    def _XRI(self, op, pc):
        self._a = t = self._a ^ self._mr(pc + 1)
        self._flags.cy = False
        self._set_flags(t)
        self._pc = pc + 2

    def _PCHL(self, op, pc):
        self._pc = (self._h << 8) + self._l

    def _XCHG(self, op, pc):
        th = self._h
        tl = self._l
        self._h = self._d
        self._l = self._e
        self._d = th
        self._e = tl
        self._pc = pc + 1

    def _XTHL(self, op, pc):
        sp = self._sp
        th = self._h
        tl = self._l
        mr = self._mr
        mw = self._mw
        self._l = mr(sp)
        self._h = mr(sp + 1)
        mw(sp, tl)
        mw(sp + 1, th)
        self._pc = pc + 1

    def _PUSHPSW(self, op, pc):
        f = self._flags
        sp = self._sp
        mw = self._mw
        p = 0x02
        if f.cy:
            p |= 0x01
        if f.p:
            p |= 0x04
        if f.ac:
            p |= 0x10
        if f.z:
            p |= 0x40
        if f.s:
            p |= 0x80
        mw(sp - 1, self._a)
        mw(sp - 2, p)
        self._sp = (sp - 2) & 0xffff
        self._pc = pc + 1

    def _POPPSW(self, op, pc):
        f = self._flags
        sp = self._sp
        mr = self._mr
        p = mr(sp)
        self._a = mr(sp + 1)
        f.cy = (p & 0x01) != 0x00
        f.p  = (p & 0x04) != 0x00
        f.ac = (p & 0x10) != 0x00
        f.z  = (p & 0x40) != 0x00
        f.s  = (p & 0x80) != 0x00
        self._sp = (sp + 2) & 0xffff
        self._pc = pc + 1

    def _SPHL(self, op, pc):
        self._sp = (self._h << 8) + self._l
        self._pc = pc + 1

    def _EI(self, op, pc):
        self._ie = True
        self._pc = pc + 1

    def _DI(self, op, pc):
        self._ie = False
        self._pc = pc + 1

    def _default_cntl(self, op, pc):
        f = self._default_cntl_map[op & 0x0f]
        if f is None:
            print("unknown opcode: %02x" % op)
            self.halt()
            return
        f(op, pc, self._sp)
        
    def _PUSH(self, op, pc, sp):
        mw = self._mw
        (x0, x1) = self._rp_read((op & 0x30) >> 4)
        mw(sp - 1, x1)
        mw(sp - 2, x0)
        self._sp = (sp - 2) & 0xffff
        self._pc = pc + 1
        
    def _POP(self, op, pc, sp):
        mr = self._mr
        x0 = mr(sp)
        x1 = mr(sp + 1)
        self._sp = (sp + 2) & 0xffff
        self._rp_write((op & 0x30) >> 4, x0, x1)
        self._pc = pc + 1
        
    def _Jc(self, op, pc, sp): 
        if self._check_flags((op & 0x38) >> 3):
            mr = self._mr
            self._pc = mr(pc + 1) + (mr(pc + 2) << 8)
        else:
            self._pc = pc + 3
            
    def _Cc(self, op, pc, sp):
        if self._check_flags((op & 0x38) >> 3):
            an = pc + 3
            mw = self._mw
            mr = self._mr
            mw(sp - 1, an >> 8)
            mw(sp - 2, an & 0xff)
            self._sp = (sp - 2) & 0xffff
            self._pc = mr(pc + 1) + (mr(pc + 2) << 8)
        else:
            self._pc = pc + 3
            
    def _Rc(self, op, pc, sp):
        if self._check_flags((op & 0x38) >> 3):
            mr = self._mr
            self._pc = mr(sp) + (mr(sp + 1) << 8) 
            self._sp = (sp + 2) & 0xffff
        else:
            self._pc = pc + 1
            
    def _RST(self, op, pc, sp):
        if not self._intr_pc:
            pc += 1
        else:
            self._intr_pc = False
        mw = self._mw
        mw(sp - 1, pc >> 8)
        mw(sp - 2, pc & 0xff)
        self._sp = (sp - 2) & 0xffff
        self._pc = op & 0x38         
            
    def _set_flags(self, value):
        f = self._flags
        f.z = value == 0x00
        f.s = (value & 0x80) != 0x00
        n = 0
        m = 0x80
        for i in self._rng8:
            if value & m:
                n += 1
            m >>= 1
        f.p = (n & 0x01) == 0x00

    def _check_flags(self, code):
        f = self._flags
        if code == 0:
            return not f.z
        elif code == 1:
            return f.z
        elif code == 2:
            return not f.cy
        elif code == 3:
            return f.cy
        elif code == 4:
            return not f.p
        elif code == 5:
            return f.p
        elif code == 6:
            return not f.s
        else:
            return f.s

    def _reg_read(self, code):
        return getattr(self, self._reg_map[code])

    def _reg_write(self, code, value):
        setattr(self, self._reg_map[code], value)

    def _rp_write(self, code, value0, value1):
        if code == 0:
            self._b = value1
            self._c = value0
        elif code == 1:
            self._d = value1
            self._e = value0
        elif code == 2:
            self._h = value1
            self._l = value0
        else:
            self._sp = (value1 << 8) + value0

    def _rp_read(self, code):
        if code == 0:
            return (self._c, self._b)
        elif code == 1:
            return (self._e, self._d)
        elif code == 2:
            return (self._l, self._h)
        else:
            return (self._sp & 0xff, self._sp >> 8)

    def _rp_incr(self, code):
        if code == 0:
            t = self._c + 1
            if t > 255:
                self._c = 0
                self._b = (self._b + 1) & 0xff
            else:
                self._c = t
        elif code == 1:
            t = self._e + 1
            if t > 255:
                self._e = 0
                self._d = (self._d + 1) & 0xff
            else:
                self._e = t
        elif code == 2:
            t = self._l + 1
            if t > 255:
                self._l = 0
                self._h = (self._h + 1) & 0xff
            else:
                self._l = t
        else:
            self._sp = (self._sp + 1) & 0xffff

    def _rp_decr(self, code):
        if code == 0:
            t = self._c - 1
            if t < 0:
                self._c = 255
                self._b = (self._b - 1) & 0xff
            else:
                self._c = t
        elif code == 1:
            t = self._e - 1
            if t < 0:
                self._e = 255
                self._d = (self._d - 1) & 0xff
            else:
                self._e = t
        elif code == 2:
            t = self._l - 1
            if t < 0:
                self._l = 255
                self._h = (self._h - 1) & 0xff
            else:
                self._l = t
        else:
            self._sp = (self._sp - 1) & 0xffff
        

    def _print_state(self):
        print("A=%02x B=%02x C=%02x D=%02x E=%02x H=%02x L=%02x" % \
              (self._a, self._b, self._c, self._d, self._e, self._h, self._l))
        print("PC=%04x SP=%04x" % (self._pc, self._sp))
        print("Z=%d S=%d CY=%d AC=%d P=%d (I)=%d" % \
              (self._flags.z, self._flags.s, self._flags.cy,
               self._flags.ac, self._flags.p, self._ie))
        print()

    
        
class i8085(i8080): 
    """
    Intel 8085 processor
    """
    pass
        
