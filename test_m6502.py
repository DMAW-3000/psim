
import unittest

from memory import *
from cpu.m6502 import *


class Test_m6502(unittest.TestCase):

    def setUp(self):
        self._mem = AddressSpace()
        self._ram = RAM(512)
        self._mem.add(0x0000, self._ram, "TRAM")
        romData = (0x0000, 0x0000)
        self._rom = DROM(4, romData)
        self._mem.add(0xfffc, self._rom, "TROM")
        self._proc = m6502(self._mem)
        
    def clear(self):
        self._proc.reset()
        self.clear_regs()
        self.clear_flags()
        self.clear_ram()
        
    def clear_regs(self):
        self._proc._a = 0x00
        self._proc._x = 0x00
        self._proc._y = 0x00
        self._proc._sp = 0xff
        
    def clear_flags(self):
        self._proc._flags.n = False
        self._proc._flags.v = False
        self._proc._flags.b = False
        self._proc._flags.d = False
        self._proc._flags.i = False
        self._proc._flags.z = False
        self._proc._flags.c = False
        
    def clear_ram(self):
        for n in range(self._ram.size()):
            self._ram._m[n] = 0x00
        
    def test_reset(self):
        self._proc.reset()
        self.assertEqual(self._proc._pc, 0x0000)
        self.assertEqual(self._proc._sp, 0xfd)
        self.assertTrue(self._proc._flags.i)
        
    def test_nop(self):
        self.clear()
        self._ram._m[0] = 0xea
        self._proc._step()
        self.assertEqual(self._proc._a, 0x00)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_cli(self):
        self.clear()
        self._ram._m[0] = 0x58
        self._proc._flags.i = True
        self._proc._step()
        self.assertFalse(self._proc._flags.i)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_cld(self):
        self.clear()
        self._ram._m[0] = 0xd8
        self._proc._flags.d = True
        self._proc._step()
        self.assertFalse(self._proc._flags.d)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_clc(self):
        self.clear()
        self._ram._m[0] = 0x18
        self._proc._flags.c = True
        self._proc._step()
        self.assertFalse(self._proc._flags.c)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_sec(self):
        self.clear()
        self._ram._m[0] = 0x38      # SEC
        self._proc._step()
        self.assertTrue(self._proc._flags.c)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_sed(self):
        self.clear()
        self._ram._m[0] = 0xf8      # SED
        self._proc._step()
        self.assertTrue(self._proc._flags.d)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_lda(self):
        self.clear()
        self._ram._m[0] = 0xa9      # LDA #$68
        self._ram._m[1] = 0x68
        self._ram._m[2] = 0xa5      # LDA $10
        self._ram._m[3] = 0x10
        self._ram._m[4] = 0xad      # LDA $0103
        self._ram._m[5] = 0x03
        self._ram._m[6] = 0x01
        self._ram._m[16] = 0x71
        self._ram._m[259] = 0xa1
        self._proc._step()
        self.assertEqual(self._proc._a, 0x68)
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0002)
        self._proc._step()
        self.assertEqual(self._proc._a, 0x71)
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0004)
        self._proc._step()
        self.assertEqual(self._proc._a, 0xa1)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0007)
        
    def test_ldy(self):
        self.clear()
        self._ram._m[0] = 0xa0      # LDY #$68
        self._ram._m[1] = 0x68
        self._ram._m[2] = 0xa4      # LDY $10
        self._ram._m[3] = 0x10
        self._ram._m[16] = 0x71
        self._proc._step()
        self.assertEqual(self._proc._y, 0x68)
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0002)
        self._proc._step()
        self.assertEqual(self._proc._y, 0x71)
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0004)
        
    def test_ldx(self):
        self.clear()
        self._ram._m[0] = 0xa2      # LDX #$68
        self._ram._m[1] = 0x68
        self._ram._m[2] = 0xa6      # LDX $10
        self._ram._m[3] = 0x10
        self._ram._m[16] = 0x71
        self._proc._step()
        self.assertEqual(self._proc._x, 0x68)
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0002)
        self._proc._step()
        self.assertEqual(self._proc._x, 0x71)
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0004)
        
    def test_sty(self):
        self.clear()
        self._ram._m[0] = 0x84      # STY $10
        self._ram._m[1] = 0x10
        self._proc._y = 0xb3
        self._proc._step()
        self.assertEqual(self._ram._m[16], 0xb3)
        self.assertEqual(self._proc._pc, 0x0002)
        
    def test_sta(self):
        self.clear()
        self._ram._m[0] = 0x85      # STA $10
        self._ram._m[1] = 0x10
        self._ram._m[2] = 0x95      # STA $10, X
        self._ram._m[3] = 0x10
        self._ram._m[4] = 0x8d      # STA $101
        self._ram._m[5] = 0x01
        self._ram._m[6] = 0x01
        self._proc._a = 0x7a
        self._proc._step()
        self.assertEqual(self._ram._m[16], 0x7a)
        self.assertEqual(self._proc._pc, 0x0002)
        self._proc._a = 0x69
        self._proc._x = 0x01
        self._proc._step()
        self.assertEqual(self._ram._m[17], 0x69)
        self.assertEqual(self._proc._pc, 0x0004)
        self._proc._a = 0x12
        self._proc._step()
        self.assertEqual(self._ram._m[257], 0x12)
        self.assertEqual(self._proc._pc, 0x0007)
        
    def test_dex(self):
        self.clear()
        self._ram._m[0] = 0xca      # DEX
        self._ram._m[1] = 0xca      # DEX
        self._proc._x = 0x01
        self._proc._step()
        self.assertEqual(self._proc._x, 0x00)
        self.assertTrue(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self._proc._step()
        self.assertEqual(self._proc._x, 0xff)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.n)
        self.assertTrue(self._proc._pc, 0x0002)
        
    def test_dey(self):
        self.clear()
        self._ram._m[0] = 0x88      # DEY
        self._ram._m[1] = 0x88      # DEY
        self._proc._y = 0x01
        self._proc._step()
        self.assertEqual(self._proc._y, 0x00)
        self.assertTrue(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self._proc._step()
        self.assertEqual(self._proc._y, 0xff)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.n)
        self.assertTrue(self._proc._pc, 0x0002)
        
    def test_iny(self):
        self.clear()
        self._ram._m[0] = 0xc8      # INY
        self._ram._m[1] = 0xc8      # INY
        self._proc._y = 0xff
        self._proc._step()
        self.assertEqual(self._proc._y, 0x00)
        self.assertTrue(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self._proc._step()
        self.assertEqual(self._proc._y, 0x01)
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self.assertTrue(self._proc._pc, 0x0002)
        
    def test_tay(self):
        self.clear()
        self._ram._m[0] = 0xa8
        self._proc._a = 0xf2
        self._proc._step()
        self.assertEqual(self._proc._y, 0xf2)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_tax(self):
        self.clear()
        self._ram._m[0] = 0xaa
        self._proc._a = 0xf2
        self._proc._step()
        self.assertEqual(self._proc._x, 0xf2)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_tsx(self):
        self.clear()
        self._ram._m[0] = 0xba
        self._proc._sp = 0xf2
        self._proc._step()
        self.assertEqual(self._proc._x, 0xf2)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_txs(self):
        self.clear()
        self._ram._m[0] = 0x9a
        self._proc._x = 0xf2
        self._proc._step()
        self.assertEqual(self._proc._sp, 0xf2)
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_tya(self):
        self.clear()
        self._ram._m[0] = 0x98
        self._proc._y = 0xf2
        self._proc._step()
        self.assertEqual(self._proc._a, 0xf2)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_txa(self):
        self.clear()
        self._ram._m[0] = 0x8a
        self._proc._x = 0xf2
        self._proc._step()
        self.assertEqual(self._proc._a, 0xf2)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_bmi(self):
        self.clear()
        self._ram._m[0] = 0x30      # BMI $06
        self._ram._m[1] = 0x06  
        self._ram._m[8] = 0x30      # BMI $06
        self._ram._m[9] = 0x06     
        self._proc._flags.n = True
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0008)
        self._proc._flags.n = False
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x000a)
        
    def test_bpl(self):
        self.clear()
        self._ram._m[0] = 0x10      # BPL $06
        self._ram._m[1] = 0x06  
        self._ram._m[8] = 0x10      # BPL $06
        self._ram._m[9] = 0x06     
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0008)
        self._proc._flags.n = True
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x000a)
        
    def test_beq(self):
        self.clear()
        self._ram._m[0] = 0xf0      # BEQ $06
        self._ram._m[1] = 0x06  
        self._ram._m[8] = 0xf0      # BEQ $06
        self._ram._m[9] = 0x06     
        self._proc._flags.z = True
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0008)
        self._proc._flags.z = False
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x000a)
        
    def test_bne(self):
        self.clear()
        self._ram._m[0] = 0xd0      # BNE $06
        self._ram._m[1] = 0x06  
        self._ram._m[8] = 0xd0      # BNE $06
        self._ram._m[9] = 0x06     
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0008)
        self._proc._flags.z = True
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x000a)
        
    def test_bcs(self):
        self.clear()
        self._ram._m[0] = 0xb0      # BCS $06
        self._ram._m[1] = 0x06  
        self._ram._m[8] = 0xb0      # BCS $06
        self._ram._m[9] = 0x06
        self._proc._flags.c = True
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0008)
        self._proc._flags.c = False
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x000a)
        
    def test_bcc(self):
        self.clear()
        self._ram._m[0] = 0x90      # BCC $06
        self._ram._m[1] = 0x06  
        self._ram._m[8] = 0x90      # BCC $06
        self._ram._m[9] = 0x06     
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0008)
        self._proc._flags.c = True
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x000a)
        
    def test_jmp(self):
        self.clear()
        self._ram._m[0] = 0x4c      # JMP $0102
        self._ram._m[1] = 0x02
        self._ram._m[2] = 0x01
        self._ram._m[258] = 0xea    # NOP
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0102)
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0103)
        
    def test_jsr(self):
        self.clear()
        self._ram._m[0] = 0x20      # JSR $0010
        self._ram._m[1] = 0x10
        self._ram._m[2] = 0x00
        self._ram._m[16] = 0xea     # NOP
        self._proc._sp = 0xff
        self._proc._step()
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0011)
        self.assertEqual(self._proc._sp, 0xfd)
        self.assertEqual(self._ram._m[511], 0x00)
        self.assertEqual(self._ram._m[510], 0x02)
        
    def test_rts(self):
        self.clear()
        self._ram._m[0] = 0x60      # RTS
        self._ram._m[511] = 0x00
        self._ram._m[510] = 0x0f
        self._ram._m[16] = 0xea     # NOP
        self._proc._sp = 0xfd
        self._proc._step()
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0011)
        self.assertEqual(self._proc._sp, 0xff)
        
    def test_adc(self):
        self.clear()
        self._ram._m[0] = 0x69      # ADC #$78
        self._ram._m[1] = 0x78
        self._ram._m[2] = 0x65      # ADC $20
        self._ram._m[3] = 0x20
        self._ram._m[4] = 0x69      # ADC #$C0
        self._ram._m[5] = 0xc0
        self._ram._m[6] = 0x65      # ADC $21
        self._ram._m[7] = 0x21
        self._ram._m[32] = 0x10
        self._ram._m[33] = 0x05
        self._proc._step()
        self.assertEqual(self._proc._a, 0x78)
        self.assertFalse(self._proc._flags.c)
        self._proc._step()
        self.assertEqual(self._proc._a, 0x88)
        self.assertFalse(self._proc._flags.c)
        self._proc._flags.c = True
        self._proc._step()
        self.assertEqual(self._proc._a, 0x49)
        self.assertTrue(self._proc._flags.c)
        self._proc._step()
        self.assertEqual(self._proc._a, 0x4f)
        self.assertFalse(self._proc._flags.c)
        self.assertEqual(self._proc._pc, 0x0008)
        
    def test_cmp(self):
        self.clear()
        self._ram._m[0] = 0xc9      # CMP #$05
        self._ram._m[1] = 0x05
        self._ram._m[2] = 0xc5      # CMP $20
        self._ram._m[3] = 0x20
        self._ram._m[4] = 0xd5      # CMP $20,X
        self._ram._m[5] = 0x20
        self._ram._m[32] = 0xf9
        self._ram._m[33] = 0xb3
        self._proc._a = 0xb3
        self._proc._step()
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.c)
        self._proc._step()
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.c)
        self._proc._x = 0x01
        self._proc._step()
        self.assertTrue(self._proc._flags.z)
        self.assertTrue(self._proc._flags.c)
        self.assertEqual(self._proc._pc, 0x0006)
        
    def test_and(self):
        self.clear()
        self._ram._m[0] = 0x29      # AND #$45
        self._ram._m[1] = 0x45
        self._proc._a = 0xff
        self._proc._step()
        self.assertEqual(self._proc._a, 0x45)
        self.assertEqual(self._proc._pc, 0x0002)
        
    def test_ora(self):
        self.clear()
        self._ram._m[0] = 0x09      # ORA #$6d
        self._ram._m[1] = 0x6d
        self._ram._m[2] = 0x05      # ORA $20
        self._ram._m[3] = 0x20
        self._ram._m[32] = 0x10
        self._proc._step()
        self.assertEqual(self._proc._a, 0x6d)
        self._proc._step()
        self.assertEqual(self._proc._a, 0x7d)
        self.assertEqual(self._proc._pc, 0x0004)
        
    def test_bit(self):
        self.clear()
        self._ram._m[0] = 0x24      # BIT $20
        self._ram._m[1] = 0x20
        self._ram._m[2] = 0x2c      # BIT $0105
        self._ram._m[3] = 0x05
        self._ram._m[4] = 0x01
        self._ram._m[32] = 0x80
        self._ram._m[261] = 0x40
        self._proc._step()
        self.assertTrue(self._proc._flags.n)
        self.assertFalse(self._proc._flags.v)
        self.assertFalse(self._proc._flags.z)
        self._proc._step()
        self.assertFalse(self._proc._flags.n)
        self.assertTrue(self._proc._flags.v)
        self.assertFalse(self._proc._flags.z)
        self.assertEqual(self._proc._pc, 0x0005)
        
    def test_asl(self):
        self.clear()
        self._ram._m[0] = 0x0a      # ASL A
        self._ram._m[1] = 0x06      # ASL $20
        self._ram._m[2] = 0x20
        self._ram._m[32] = 0x42
        self._proc._a = 0x81
        self._proc._step()
        self.assertEqual(self._proc._a, 0x02)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.c)
        self._proc._step()
        self.assertEqual(self._ram._m[32], 0x84)
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.c)
        self.assertEqual(self._proc._pc, 0x0003)
        
    def test_lsr(self):
        self.clear()
        self._ram._m[0] = 0x4a      # LSR A
        self._proc._a = 0x81
        self._proc._step()
        self.assertEqual(self._proc._a, 0x40)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.c)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_ror(self):
        self.clear()
        self._ram._m[0] = 0x6a      # ROR A
        self._ram._m[1] = 0x66      # ROR $20
        self._ram._m[2] = 0x20
        self._ram._m[32] = 0x42
        self._proc._a = 0x81
        self._proc._step()
        self.assertEqual(self._proc._a, 0x40)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.c)
        self._proc._step()
        self.assertEqual(self._ram._m[32], 0xa1)
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.c)
        
    def test_inc(self):
        self.clear()
        self._ram._m[0] = 0xe6      # INC $20
        self._ram._m[1] = 0x20
        self._ram._m[32] = 0xfe
        self._proc._step()
        self.assertEqual(self._ram._m[32], 0xff)
        self.assertFalse(self._proc._flags.z)
        self.assertTrue(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0002)
        
    def test_dec(self):
        self.clear()
        self._ram._m[0] = 0xc6      # DEC $20
        self._ram._m[1] = 0x20
        self._ram._m[32] = 0x02
        self._proc._step()
        self.assertEqual(self._ram._m[32], 0x01)
        self.assertFalse(self._proc._flags.z)
        self.assertFalse(self._proc._flags.n)
        self.assertEqual(self._proc._pc, 0x0002)
        
    def test_pha(self):
        self.clear()
        self._ram._m[0] = 0x48      # PHA
        self._ram._m[1] = 0x48      # PHA
        self._proc._sp = 0xff
        self._proc._a = 0x56
        self._proc._step()
        self.assertEqual(self._proc._sp, 0xfe)
        self.assertEqual(self._ram._m[511], 0x56)
        self._proc._a = 0x1c
        self._proc._step()
        self.assertEqual(self._proc._sp, 0xfd)
        self.assertEqual(self._ram._m[510], 0x1c)
        self.assertEqual(self._proc._pc, 0x0002)
        
    def test_pla(self):
        self.clear()
        self._ram._m[0] = 0x68      # PLA
        self._ram._m[1] = 0x68      # PLA
        self._ram._m[510] = 0x56
        self._ram._m[511] = 0x1c
        self._proc._sp = 0xfd
        self._proc._step()
        self.assertEqual(self._proc._sp, 0xfe)
        self.assertEqual(self._proc._a, 0x56)
        self._proc._a = 0x1c
        self._proc._step()
        self.assertEqual(self._proc._sp, 0xff)
        self.assertEqual(self._proc._a, 0x1c)
        self.assertEqual(self._proc._pc, 0x0002)
        
        
if __name__ == '__main__':
   
   unittest.main()