
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
        self._proc._step()
        self.assertFalse(self._proc._flags.i)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_cld(self):
        self.clear()
        self._ram._m[0] = 0xd8
        self._proc._step()
        self.assertFalse(self._proc._flags.d)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_clc(self):
        self.clear()
        self._ram._m[0] = 0x18
        self._proc._step()
        self.assertFalse(self._proc._flags.c)
        self.assertEqual(self._proc._pc, 0x0001)
        
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
        
        
if __name__ == '__main__':
   
   unittest.main()