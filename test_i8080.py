
import unittest

from memory import *
from cpu.i8080 import i8080


class Test_i8080(unittest.TestCase):

    def setUp(self):
        self._mem = AddressSpace()
        self._ram = RAM(32)
        self._mem.add(0x0000, self._ram, "TRAM")
        self._io  = AddressSpace()
        self._ports = RAM(32)
        self._io.add(0x0000, self._ports, "TIOP")
        self._proc = i8080(self._mem, self._io)
        
    def clear(self):
        self._proc.reset()
        self.clear_regs()
        self.clear_flags()
        self.clear_ram()
        self.clear_ports()
        
    def clear_regs(self):
        self._proc._a = 0x00
        self._proc._b = 0x00
        self._proc._c = 0x00
        self._proc._d = 0x00
        self._proc._e = 0x00
        self._proc._h = 0x00
        self._proc._l = 0x00
        self._proc._sp = 0x0000
        
    def clear_flags(self):
        self._proc._flags.z = False
        self._proc._flags.s = False
        self._proc._flags.p = False
        self._proc._flags.cy = False
        self._proc._flags.ac = False
        
    def clear_ram(self):
        for n in range(self._ram.size()):
            self._ram._m[n] = 0x00
            
    def clear_ports(self):
        for n in range(self._ports.size()):
            self._ports._m[n] = 0x00
        
    def test_reset(self):
        self._proc.reset()
        self.assertEqual(self._proc._pc, 0x0000)
        self.assertFalse(self._proc._ie)
        
    def test_nop(self):
        self.clear()
        self._ram._m[0] = 0x00
        self._proc._step()
        self.assertEqual(self._proc._a, 0x00)
        self.assertEqual(self._proc._pc, 0x0001)
        
    def test_inc(self):
        self.clear()
        self._ram._m[0] = 0x2c
        self._ram._m[1] = 0x2c
        self._ram._m[2] = 0x24
        self._ram._m[3] = 0x24
        self._ram._m[4] = 0x24
        for n in range(5):
            self._proc._step()
        self.assertEqual(self._proc._pc, 0x0005)
        self.assertEqual(self._proc._l, 0x02)
        self.assertEqual(self._proc._h, 0x03)
        
    def test_dec(self):
        self.clear()
        self._ram._m[0] = 0x05
        self._ram._m[1] = 0x05
        self._ram._m[2] = 0x1d
        self._ram._m[3] = 0x1d
        self._ram._m[4] = 0x1d
        for n in range(5):
            self._proc._step()
        self.assertEqual(self._proc._pc, 0x0005)
        self.assertEqual(self._proc._b, 0xfe)
        self.assertEqual(self._proc._e, 0xfd)
        
    def test_mov(self):
        self.clear()
        self._ram._m[0] = 0x42
        self._ram._m[1] = 0x70
        self._proc._d = 0xa5
        self._proc._h = 0x00
        self._proc._l = 0x10
        self._proc._step()
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0002)
        self.assertEqual(self._proc._b, 0xa5)
        self.assertEqual(self._ram._m[0x0010], 0xa5)
        
    def test_add(self):
        self.clear()
        self._ram._m[0] = 0x82      # ADD D
        self._ram._m[1] = 0x83      # ADD E
        self._proc._d = 0x81
        self._proc._e = 0x82
        self._proc._step()
        self.assertEqual(self._proc._a, 0x81)
        self.assertFalse(self._proc._flags.cy)
        self._proc._step()
        self.assertEqual(self._proc._a, 0x03)
        self.assertTrue(self._proc._flags.cy)
        self.assertEqual(self._proc._pc, 0x0002)
        
    def test_adc(self):
        self.clear()
        self._ram._m[0] = 0x8a      # ADC D
        self._ram._m[1] = 0x8b      # ADC E
        self._proc._flags.cy = True
        self._proc._d = 0x81
        self._proc._e = 0x82
        self._proc._step()
        self.assertEqual(self._proc._a, 0x82)
        self.assertFalse(self._proc._flags.cy)
        self._proc._step()
        self.assertEqual(self._proc._a, 0x04)
        self.assertTrue(self._proc._flags.cy)
        self.assertEqual(self._proc._pc, 0x0002)
        
    def test_adi(self):
        self.clear()
        self._ram._m[0] = 0xc6      # ADI
        self._ram._m[1] = 0x81
        self._ram._m[2] = 0xc6      # ADI
        self._ram._m[3] = 0x82
        self._proc._step()
        self.assertEqual(self._proc._a, 0x81)
        self.assertFalse(self._proc._flags.cy)
        self._proc._step()
        self.assertEqual(self._proc._a, 0x03)
        self.assertTrue(self._proc._flags.cy)
        self.assertEqual(self._proc._pc, 0x0004)
        
    def test_push(self):
        self.clear()
        self._ram._m[0] = 0xc5      # PUSH B
        self._proc._b = 0x43
        self._proc._c = 0x26
        self._proc._sp = 0x0020
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0001)
        self.assertEqual(self._proc._sp, 0x001e)
        self.assertEqual(self._ram._m[31], 0x43)
        self.assertEqual(self._ram._m[30], 0x26)
        
    def test_pop(self):
        self.clear()
        self._ram._m[0] = 0xe1      # POP H
        self._ram._m[30] = 0x26
        self._ram._m[31] = 0x43
        self._proc._sp = 0x001e
        self._proc._step()
        self.assertEqual(self._proc._l, 0x26)
        self.assertEqual(self._proc._h, 0x43)
        self.assertEqual(self._proc._pc, 0x0001)
        self.assertEqual(self._proc._sp, 0x0020)
        
    def test_ora(self):
        self.clear()
        self._ram._m[0] = 0xb4      # ORA
        self._proc._a = 0x14
        self._proc._h = 0x26
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0001)
        self.assertEqual(self._proc._a, 0x36)
        self.assertFalse(self._proc._flags.cy)
        
    def test_lxi(self):
        self.clear()
        self._ram._m[0] = 0x11      # LXI D
        self._ram._m[1] = 0xa6
        self._ram._m[2] = 0x13
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0003)
        self.assertEqual(self._proc._d, 0x13)
        self.assertEqual(self._proc._e, 0xa6)
        
    def test_mvi(self):
        self.clear()
        self._ram._m[0] = 0x3e      # MVI A
        self._ram._m[1] = 0xf4
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0002)
        self.assertEqual(self._proc._a, 0xf4)
        
    def test_inx(self):
        self.clear()
        self._ram._m[0] = 0x03      # INX B
        self._proc._c = 0xff
        self._proc._b = 0x01
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0001)
        self.assertEqual(self._proc._c, 0x00)
        self.assertEqual(self._proc._b, 0x02)
        
    def test_dex(self):
        self.clear()
        self._ram._m[0] = 0x0b      # DCX B
        self._proc._c = 0x00
        self._proc._b = 0x02
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0001)
        self.assertEqual(self._proc._c, 0xff)
        self.assertEqual(self._proc._b, 0x01)
        
    def test_jmp(self):
        self.clear()
        self._ram._m[0] = 0xc3      # JMP
        self._ram._m[1] = 0x01
        self._ram._m[2] = 0xfe
        self._proc._step()
        self.assertEqual(self._proc._pc, 0xfe01)
        
    def test_call(self):
        self.clear()
        self._ram._m[0] = 0xcd      # CALL  
        self._ram._m[1] = 0x10
        self._ram._m[2] = 0x00
        self._ram._m[16] = 0x00     # NOP
        self._proc._sp = 0x0020
        self._proc._step()
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0011)
        self.assertEqual(self._proc._sp, 0x001e)
        self.assertEqual(self._ram._m[31], 0x00)
        self.assertEqual(self._ram._m[30], 0x03)
        
    def test_rst(self):
        self.clear()
        self._ram._m[0] = 0xcf      # RST0
        self._ram._m[8] = 0x00      # NOP
        self._proc._sp = 0x0020
        self._proc._step()
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0009)
        self.assertEqual(self._proc._sp, 0x001e)
        self.assertEqual(self._ram._m[31], 0x00)
        self.assertEqual(self._ram._m[30], 0x01)
        
    def test_ret(self):
        self.clear()
        self._ram._m[0] = 0xc9      # RET
        self._ram._m[31] = 0x00
        self._ram._m[30] = 0x10
        self._ram._m[16] = 0x00     # NOP
        self._proc._sp = 0x001e
        self._proc._step()
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0011)
        self.assertEqual(self._proc._sp, 0x0020)
        
    def test_shld(self):
        self.clear()
        self._ram._m[0] = 0x22      # SHLD
        self._ram._m[1] = 0x10
        self._ram._m[2] = 0x00
        self._proc._l = 0x46
        self._proc._h = 0x2b
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0003)
        self.assertEqual(self._ram._m[16], 0x46)
        self.assertEqual(self._ram._m[17], 0x2b)
        
    def test_lhld(self):
        self.clear()
        self._ram._m[0] = 0x2a      # LHLD
        self._ram._m[1] = 0x10
        self._ram._m[2] = 0x00
        self._ram._m[16] = 0x33
        self._ram._m[17] = 0x2f
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0003)
        self.assertEqual(self._proc._l, 0x33)
        self.assertEqual(self._proc._h, 0x2f)
        
    def test_lda(self):
        self.clear()
        self._ram._m[0] = 0x3a      # LDA 0x0012
        self._ram._m[1] = 0x12
        self._ram._m[2] = 0x00
        self._ram._m[18] = 0xd1
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0003)
        self.assertEqual(self._proc._a, 0xd1)
        
    def test_ldax(self):
        self.clear()
        self._ram._m[0] = 0x0a      # LDAX B
        self._proc._c = 0x12
        self._proc._b = 0x00
        self._ram._m[18] = 0xd1
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0001)
        self.assertEqual(self._proc._a, 0xd1)
        
    def test_sta(self):
        self.clear()
        self._ram._m[0] = 0x32      # STA 0x0012
        self._ram._m[1] = 0x12
        self._ram._m[2] = 0x00
        self._proc._a = 0xd1
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0003)
        self.assertEqual(self._ram._m[18], 0xd1)
        
    def test_ei(self):
        self.clear()
        self._ram._m[0] = 0xfb      # EI
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0001)
        self.assertTrue(self._proc._ie)
        
    def test_di(self):
        self.clear()
        self._ram._m[0] = 0xf3      # DI
        self._proc._ie = True
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0001)
        self.assertFalse(self._proc._ie)
        
    def test_halt(self):
        self.clear()
        self._ram._m[0] = 0x76      # HLT
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0000)
        self.assertTrue(self._proc.halted())
        
    def test_pchl(self):
        self.clear()
        self._ram._m[0] = 0xe9      # PCHL
        self._ram._m[16] = 0x00     # NOP
        self._proc._l = 0x10
        self._proc._h = 0x00
        self._proc._step()
        self._proc._step()
        self.assertEqual(self._proc._pc, 0x0011)
        
       
if __name__ == '__main__':
   
   unittest.main()