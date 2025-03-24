                    
from processor import *

class m6502(Processor):

    class _Flags(object):

        def __init__(self):
            self.n = False
            self.v = False
            self.b = False
            self.d = False
            self.i = False
            self.z = False
            self.c = False
            

    def __init__(self, memAs, clkMod = 3, clkOut = None):
        Processor.__init__(self, clkMod, clkOut)
        
        self._flags = self._Flags()
        self._mem = memAs
        self._addr_mask = 0xffff
        self._stack_addr = 0x0100
        
        self._pc = 0
        self._a = 0
        self._x = 0
        self._y = 0
        self._sp = 0xff

        self._op_map = [None] * 256
        m = self._op_map

        m[0xa9] = self._LDAimm
        m[0xa5] = self._LDAzp
        m[0xb5] = self._LDAzpx
        m[0xad] = self._LDAabs
        #self._op_map[0xbd] = self._LDA
        m[0xb9] = self._LDAabsy
        #self._op_map[0xa1] = self._LDA
        #self._op_map[0xb1] = self._LDA

        m[0x85] = self._STAzp
        m[0x95] = self._STAzpx
        m[0x8d] = self._STAabs
        #self._op_map[0x9d] = self._STA
        #self._op_map[0x99] = self._STA
        #self._op_map[0x81] = self._STA
        #self._op_map[0x91] = self._STA
        
        m[0xa2] = self._LDXimm
        m[0xa6] = self._LDXzp
        #self._op_map[0xb6] = self._LDX
        #self._op_map[0xae] = self._LDX
        #self._op_map[0xbe] = self._LDX

        m[0xa0] = self._LDYimm
        m[0xa4] = self._LDYzp
        #self._op_map[0xb4] = self._LDY
        #self._op_map[0xac] = self._LDY
        #self._op_map[0xbc] = self._LDY

        m[0x84] = self._STYzp

        m[0x69] = self._ADCimm
        m[0x65] = self._ADCzp
        #self._op_map[0x75] = self._ADC
        #self._op_map[0x6d] = self._ADC
        #self._op_map[0x7d] = self._ADC
        #self._op_map[0x79] = self._ADC
        #self._op_map[0x61] = self._ADC
        #self._op_map[0x71] = self._ADC

        m[0xe5] = self._SBCzp

        m[0xc9] = self._CMPimm
        m[0xc5] = self._CMPzp
        m[0xd5] = self._CMPzpx
        #self._op_map[0xcd] = self._CMP
        #self._op_map[0xdd] = self._CMP
        #self._op_map[0xd9] = self._CMP
        #self._op_map[0xc1] = self._CMP
        #self._op_map[0xd1] = self._CMP

        m[0xc0] = self._CPYimm

        m[0xe6] = self._INCzp
        #self._op_map[0xf6] = self._INC
        #self._op_map[0xee] = self._INC
        #self._op_map[0xfe] = self._INC

        m[0xc6] = self._DECzp
        #self._op_map[0xd6] = self._DEC
        #self._op_map[0xce] = self._DEC
        #self._op_map[0xde] = self._DEC

        m[0x29] = self._ANDimm

        m[0x09] = self._ORAimm
        m[0x05] = self._ORAzp

        m[0x24] = self._BITzp
        m[0x2c] = self._BITabs

        m[0x0a] = self._ASLacc
        m[0x06] = self._ASLzp
        #self._op_map[0x16] = self._ASL
        #self._op_map[0x0e] = self._ASL
        #self._op_map[0x1e] = self._ASL

        m[0x4a] = self._LSRacc

        m[0x6a] = self._RORacc
        m[0x66] = self._RORzp
        #self._op_map[0x76] = self._ROR
        #self._op_map[0x6e] = self._ROR
        #self._op_map[0x7e] = self._ROR

        m[0x4c] = self._JMPabs
        #self._op_map[0x6c] = self._JMP

        m[0x00] = self._BRK
        m[0x18] = self._CLC
        m[0x20] = self._JSR
        m[0x30] = self._BMI
        m[0x38] = self._SEC
        m[0x48] = self._PHA
        m[0x60] = self._RTS
        m[0x68] = self._PLA
        m[0x88] = self._DEY
        m[0x78] = self._SEI
        m[0x8a] = self._TXA
        m[0x90] = self._BCC
        m[0x98] = self._TYA
        m[0x9a] = self._TXS
        m[0xa8] = self._TAY
        m[0xb0] = self._BCS
        m[0xba] = self._TSX
        m[0xca] = self._DEX
        m[0xd0] = self._BNE
        m[0xd8] = self._CLD
        m[0xea] = self._NOP
        m[0xf0] = self._BEQ
        
    def _reset(self):
        self._pc = 0x1000

    def _step(self):
        pc = self._pc
        op = self._mem_read(pc)
        f = self._op_map[op]
        if f is None:
            print("unknown opcode: %02x" % op)
            self.hlt = True
            return
        pci = f(pc)
        self._pc = (self._pc + pci) & 0xffff

    def _check_break(self, blist):
        if self._pc in blist:
            return True
        else:
            return False
            
    def _enable_log(self):
        self._mem.enable_trc()
        
    def _disable_log(self):
        self._mem.disable_trc()

    def _mem_read(self, addr):
        return self._mem.read8(addr & self._addr_mask)

    def _mem_write(self, addr, value):
        self._mem.write8(addr & self._addr_mask, value)

    def _stack_read(self, offset):
        offset = (self._sp + offset) & 0xff
        return self._mem_read(self._stack_addr + offset)

    def _stack_write(self, offset, value):
        offset = (self._sp + offset) & 0xff
        self._mem_write(self._stack_addr + offset, value)

    def _BRK(self, pc):
        self.hlt = True
        return 0

    def _LDAimm(self, pc):
        t = self._mem_read(pc + 1)
        self._a = t
        self._set_flags(t)
        return 2

    def _LDAzp(self, pc): 
        t = self._mem_read(self._mem_read(pc + 1))
        self._a = t
        self._set_flags(t)
        return 2

    def _LDAzpx(self, pc):
        a0 = (self._mem_read(pc + 1) + self._x) & 0xff
        t = self._mem_read(a0)
        self._a = t
        self._set_flags(t)
        return 2

    def _LDAabs(self, pc):
        a0 = self._mem_read(pc + 1)
        a1 = self._mem_read(pc + 2)
        t = self._mem_read((a1 << 8) + a0)
        self._a = t
        self._set_flags(t)
        return 3

    def _LDAabsy(self, pc):
        a = self._mem_read(pc + 1)
        a += (self._mem_read(pc + 2) << 8)
        t = self._mem_read((a + self._y) & 0xffff)
        self._a = t
        self._set_flags(t)
        return 3

    def _STAzp(self, pc):
        self._mem_write(self._mem_read(pc + 1), self._a)
        return 2

    def _STAzpx(self, pc):
        a0 = (self._mem_read(pc + 1) + self._x) & 0xff
        self._mem_write(a0, self._a)
        return 2

    def _STAabs(self, pc):
        a0 = self._mem_read(pc + 1)
        a1 = self._mem_read(pc + 2)
        self._mem_write((a1 << 8) + a0, self._a)
        return 3

    def _LDXimm(self, pc):
        t = self._mem_read(pc + 1)
        self._x = t
        self._set_flags(t)
        return 2

    def _LDXzp(self, pc):
        t = self._mem_read(self._mem_read(pc + 1))
        self._x = t
        self._set_flags(t)
        return 2

    def _LDYimm(self, pc):
        t = self._mem_read(pc + 1)
        self._y = t
        self._set_flags(t)
        return 2

    def _LDYzp(self, pc):
        t = self._mem_read(self._mem_read(pc + 1))
        self._y = t
        self._set_flags(t)
        return 2

    def _STYzp(self, pc):
        self._mem_write(self._mem_read(pc + 1), self._y)
        return 2

    def _ADCimm(self, pc): 
        t = self._a + self._mem_read(pc + 1) + int(self._flags.c)
        self._flags.c = (t > 255)
        t &= 0xff
        self._a = t
        self._set_flags(t)
        return 2

    def _ADCzp(self, pc):
        a0 = self._mem_read(pc + 1)
        t = self._a + self._mem_read(a0) + int(self._flags.c)
        self._flags.c = (t > 255)
        t &= 0xff
        self._a = t
        self._set_flags(t)
        return 2

    def _SBCzp(self, pc):
        a0 = self._mem_read(pc + 1)
        t = self._a - self._mem_read(a0)
        t -= int(not self._flags.c)
        self._flags.c = not (t < 0)
        t &= 0xff
        self._a = t
        self._set_flags(t)
        return 2

    def _CMPimm(self, pc): 
        t = self._a - self._mem_read(pc + 1)
        self._flags.c = (t >= 0)
        self._set_flags(t & 0xff)
        return 2

    def _CMPzp(self, pc):
        t = self._a - self._mem_read(self._mem_read(pc + 1))
        self._flags.c = (t >= 0)
        self._set_flags(t & 0xff)
        return 2

    def _CMPzpx(self, pc):
        a0 = (self._mem_read(pc + 1) + self._x) & 0xff
        t = self._a - self._mem_read(a0)
        self._flags.c = (t >= 0)
        self._set_flags(t & 0xff)
        return 2

    def _CPYimm(self, pc):
        t = self._y - self._mem_read(pc + 1)
        self._flags.c = (t >= 0)
        self._set_flags(t & 0xff)
        return 2

    def _INCzp(self, pc):
        a = self._mem_read(pc + 1)
        x0 = (self._mem_read(a) + 1) & 0xff
        self._mem_write(a, x0)
        self._set_flags(x0)
        return 2

    def _DECzp(self, pc):
        a = self._mem_read(pc + 1)
        x0 = (self._mem_read(a) - 1) & 0xff
        self._mem_write(a, x0)
        self._set_flags(x0)
        return 2

    def _ANDimm(self, pc):
        t = self._a & self._mem_read(pc + 1)
        self._a = t
        self._set_flags(t)
        return 2

    def _ORAimm(self, pc):
        t = self._a | self._mem_read(pc + 1)
        self._a = t
        self._set_flags(t)
        return 2

    def _ORAzp(self, pc):
        a0 = self._mem_read(pc + 1)
        t = self._a | self._mem_read(a0)
        self._a = t
        self._set_flags(t)
        return 2

    def _BITzp(self, pc):
        a0 = self._mem_read(pc + 1)
        t = self._a ^ self._mem_read(a0)
        f = self._flags
        f.n = ((t & 0x80) != 0)
        f.v = ((t & 0x40) != 0)
        f.z = (t == 0x00)
        return 2

    def _BITabs(self, pc):
        a0 = self._mem_read(pc + 1)
        a1 = self._mem_read(pc + 2)
        t = self._a ^ self._mem_read((a1 << 8) + a0)
        f = self._flags
        f.n = ((t & 0x80) != 0)
        f.v = ((t & 0x40) != 0)
        f.z = (t == 0)
        return 3

    def _ASLacc(self, pc):
        t = self._a
        self._flags.c = (t & 0x80)
        t = (t << 1) & 0xff
        self._a = t 
        self._set_flags(t)
        return 1

    def _ASLzp(self, pc):
        a = self._mem_read(pc + 1)
        x0 = self._mem_read(a)
        self._flags.c = ((x0 & 0x80) != 0x00)
        x0 = (x0 << 1) & 0xff
        self._mem_write(a, x0)
        self._set_flags(x0)
        return 2

    def _LSRacc(self, pc):
        t = self._a
        self._flags.c = ((t & 0x01) != 0x00)
        t >>= 1
        self._a = t
        self._set_flags(t)
        return 1

    def _RORacc(self, pc):
        f = self._flags
        t = (self._a & 0x01)
        self._a >>= 1
        if f.c:
           self._a |= 0x80
        f.c = (t != 0x00)
        self._set_flags(self._a)
        return 1

    def _RORzp(self, pc):
        f = self._flags
        a0 = self._mem_read(pc + 1)
        x0 = self._mem_read(a0)
        t = (x0 & 0x01)
        x0 >>= 1
        if f.c:
            x0 |= 0x80
        f.c = (t != 0x00)
        self._mem_write(a, x0)
        self._set_flags(x0)
        return 2
        
    def _SEI(self, pc):
        self._flags.i = True
        return 1

    def _CLD(self, pc):
        self._flags.d = False
        return 1

    def _SEC(self, pc):
        self._flags.c = True
        return 1

    def _CLC(self, pc):
        self._flags.c = False
        return 1

    def _NOP(self, pc):
        return 1

    def _TXA(self, pc):
        self._a = self._x
        self._set_flags(self._a)
        return 1

    def _TXS(self, pc):
        self._sp = self._x
        self._set_flags(self._sp)
        return 1

    def _TSX(self, pc):
        self._x = self._sp
        self._set_flags(self._x)
        return 1

    def _TYA(self, pc):
        self._a = self._y
        self._set_flags(self._a)
        return 1

    def _TAY(self, pc):
        self._y = self._a
        self._set_flags(self._y)
        return 1

    def _DEX(self, pc):
        self._x = (self._x - 1) & 0xff
        self._set_flags(self._x)
        return 1

    def _DEY(self, pc):
        self._y = (self._y - 1) & 0xff
        self._set_flags(self._y)
        return 1

    def _JSR(self, pc):
        ra = (pc + 2) & 0xffff
        self._stack_write( 0, ra >> 8)
        self._stack_write(-1, ra & 0xff)
        self._sp = (self._sp - 2) & 0xff
        a0 = self._mem_read(pc + 1) 
        self._pc = (self._mem_read(pc + 2) << 8) + a0
        return 0

    def _RTS(self, pc):
        ra = self._stack_read(1)
        ra += (self._stack_read(2) << 8)
        self._sp = (self._sp + 2) & 0xff
        self._pc = (ra + 1) & 0xffff
        return 0

    def _JMPabs(self, pc):
        a0 = self._mem_read(pc + 1)
        self._pc = ((self._mem_read(pc + 2) << 8) + a0) & 0xffff
        return 0    

    def _PHA(self, pc):
        self._stack_write(0, self._a)
        self._sp = (self._sp - 1) & 0xff
        return 1

    def _PLA(self, pc):
        self._a = self._stack_read(1)
        self._sp = (self._sp + 1) & 0xff
        return 1

    def _BNE(self, pc):
        if not self._flags.z:
            return self._br_offset(pc)
        else:
            return 2

    def _BEQ(self, pc):
        if self._flags.z:
            return self._br_offset(pc)
        else:
            return 2

    def _BCS(self, pc):
        if self._flags.c:
            return self._br_offset(pc)
        else:
            return 2

    def _BCC(self, pc):
        if not self._flags.c:
            return self._br_offset(pc)
        else:
            return 2

    def _BMI(self, pc):
        if self._flags.n:
            return self._br_offset(pc)
        else:
            return 2

    def _br_offset(self, pc):
        o = self._mem_read(pc + 1)
        if o > 0x7f:
            return  2 - ((-o) & 0xff)
        else:
            return o + 2
            
    def _set_flags(self, value):
        f = self._flags
        f.z = (value == 0x00)
        f.n = (value & 0x80) != 0x00

    def _check_flags(self, code):
        if code == 0:
            return not self._flags.z
        elif code == 1:
            return self._flags.z
        elif code == 2:
            return not self._flags.cy
        elif code == 3:
            return self._flags.cy
        elif code == 4:
            return not self._flags.p
        elif code == 5:
            return self._flags.p
        elif code == 6:
            return not self._flags.s
        else:
            return self._flags.s

    def _print_state(self):
        print("A=%02x X=%02x Y=%02x" % \
              (self._a, self._x, self._y))
        print("PC=%04x SP=%02x" % (self._pc, self._sp))
        print("N=%d V=%d B=%d I=%d Z=%d C=%d" % \
              (self._flags.n, self._flags.v, self._flags.d,
               self._flags.i, self._flags.z, self._flags.c))
        #print("%02x %02x %02x %02x %02x" % \
        #      (self._mem.read8(self._sp - 2), self._mem.read8(self._sp - 1),
        #      self._mem.read8(self._sp), self._mem.read8(self._sp + 1),
        #      self._mem.read8(self._sp + 2)))
        print()
        

class m6507(m6502):

    def __init__(self, memAs, clkMod = 3, clkOut = None):
        m6502.__init__(self, memAs, clkMod, clkOut)
        self._addr_mask = 0x1fff
        self._stack_addr = 0x0000

        
