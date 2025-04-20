
import unittest

from memory import *
from cpu.m6502 import *


class Test_m6502(unittest.TestCase):

    def setUp(self):
        self._mem = AddressSpace()
        self._ram = RAM(32)
        self._mem.add(0x0000, self._ram, "TRAM")
        self._rom = ROM(4)
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
        self.assertEqual(self._proc._pc, 0x1000)
        
    def test_nop(self):
        self.clear()
        self._ram._m[0] = 0xea
        self._proc._step()
        self.assertEqual(self._proc._a, 0x00)
        self.assertEqual(self._proc._pc, 0x1001)
    
       
if __name__ == '__main__':
   
   unittest.main()