
from memory import *

import unittest

class Test_RAM(unittest.TestCase):

    def setUp(self):
        self._as = AddressSpace()
        self._ram = RAM(4)
        self._as.add(0, self._ram, "TRAM")
        
    def clear(self):
        self._ram._m[0] = 0x00
        self._ram._m[1] = 0x00
        self._ram._m[2] = 0x00
        self._ram._m[3] = 0x00
        
    def test_read(self):
        self.clear()
        self.assertEqual(self._as.read8(0), 0x00)
        self.assertEqual(self._as.read8(1), 0x00)
        self.assertEqual(self._as.read8(2), 0x00)
        self.assertEqual(self._as.read8(3), 0x00)
        self._ram._m[0] = 0x01
        self._ram._m[1] = 0x25
        self._ram._m[2] = 0xa4
        self._ram._m[3] = 0x5b
        self.assertEqual(self._as.read8(0), 0x01)
        self.assertEqual(self._as.read8(1), 0x25)
        self.assertEqual(self._as.read8(2), 0xa4)
        self.assertEqual(self._as.read8(3), 0x5b)
        self.assertEqual(self._as.read16le(0), 0x2501)
        self.assertEqual(self._as.read16le(2), 0x5ba4)
        self.assertEqual(self._as.read16be(0), 0x0125)
        self.assertEqual(self._as.read16be(2), 0xa45b)
        
    def test_write(self):
        self.clear()
        self._as.write8(0, 0x57)
        self._as.write8(1, 0x3d)
        self._as.write8(2, 0x80)
        self._as.write8(3, 0x2f)
        self.assertEqual(self._ram._m[0], 0x57)
        self.assertEqual(self._ram._m[1], 0x3d)
        self.assertEqual(self._ram._m[2], 0x80)
        self.assertEqual(self._ram._m[3], 0x2f)
        self.clear()
        self._as.write16le(0, 0x146d)
        self._as.write16le(2, 0x9402)
        self.assertEqual(self._ram._m[0], 0x6d)
        self.assertEqual(self._ram._m[1], 0x14)
        self.assertEqual(self._ram._m[2], 0x02)
        self.assertEqual(self._ram._m[3], 0x94)
        self.clear()
        self._as.write16be(0, 0x146d)
        self._as.write16be(2, 0x9402)
        self.assertEqual(self._ram._m[0], 0x14)
        self.assertEqual(self._ram._m[1], 0x6d)
        self.assertEqual(self._ram._m[2], 0x94)
        self.assertEqual(self._ram._m[3], 0x02)
        
        
if __name__ == '__main__':

    unittest.main()