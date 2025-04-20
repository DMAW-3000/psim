
from memory import *
import io

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
        

class Test_ROM(unittest.TestCase):

    def setUp(self):
        hexStr = "S113FF00D858A07F8C12D0A9A78D11D08D13D0C939\nS113FF10DFF013C99BF003C8100FA95C20EFFFA901"
        hexFile = io.StringIO(hexStr)
        self._as = AddressSpace()
        self._rom = ROM(32, None, 0xff00, False)
        self._rom._loadSREC(hexFile)
        self._as.add(0xff00, self._rom, "TROM")
        
    def test_read(self):
        self.assertEqual(self._as.read8(0xff00), 0xd8)
        self.assertEqual(self._as.read8(0xff01), 0x58)
        self.assertEqual(self._as.read8(0xff02), 0xA0)
        self.assertEqual(self._as.read8(0xff03), 0x7F)
        self.assertEqual(self._as.read8(0xff1e), 0xff)
        self.assertEqual(self._as.read8(0xff1f), 0xa9)
        self.assertEqual(self._as.read16le(0xff04), 0x128c)
        
    def test_write(self):
        self._as.write8(0xff00, 0x00)
        self.assertEqual(self._rom._m[0], 0xd8)
        self._as.write16le(0xff04, 0x0000)
        self.assertEqual(self._rom._m[4], 0x8c)
        self.assertEqual(self._rom._m[5], 0x12)
        self._as.write16be(0xff04, 0x0000)
        self.assertEqual(self._rom._m[4], 0x8c)
        self.assertEqual(self._rom._m[5], 0x12)
        
        
class Test_DROM(unittest.TestCase):

    def setUp(self):
        self._as = AddressSpace()
        romData = (0xa3, 0xf5, 0x01, 0x3d)
        self._rom = DROM(8, romData)
        self._as.add(0x0000, self._rom, "TROM")
        
    def test_read(self):
        self.assertEqual(self._as.read8(0), 0xa3)
        self.assertEqual(self._as.read8(1), 0xf5)
        self.assertEqual(self._as.read8(2), 0x01)
        self.assertEqual(self._as.read8(3), 0x3d)
        
    def test_write(self):
        self._as.write8(0, 0x50)
        self.assertEqual(self._rom._m[0], 0xa3)
        self._as.write16le(0, 0x5321)
        self.assertEqual(self._rom._m[0], 0xa3)
        self.assertEqual(self._rom._m[1], 0xf5)
        self._as.write16be(4, 0x5321)
        self.assertEqual(self._rom._m[4], 0x00)
        self.assertEqual(self._rom._m[5], 0x00)
        
if __name__ == '__main__':

    unittest.main()