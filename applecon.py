
import pygame
import sys
import time
import socket
from multiprocessing import shared_memory
from argparse import ArgumentParser

class APPLECON_App(object):

    def __init__(self, args):
    
        self._kbSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._kbAddr = ('127.0.0.1', args.port)
        self._kbData = bytearray(1)
        self._kbShift = False
        
        self._port = shared_memory.SharedMemory("VMEM_APPLE1", True, 1)
        self._vram = bytearray(4096)
        c = ord(' ')
        for n in range(len(self._vram)):
            self._vram[n] = c
            
        self._cblack = pygame.Color(0, 0, 0)
        self._cgreen = pygame.Color(0, 255, 0)
        self._cred   = pygame.Color(255, 0, 0)
        
        self._kb_map_lower = {
            pygame.K_1          : ord('1'),
            pygame.K_2          : ord('2'),
            pygame.K_3          : ord('3'),
            pygame.K_4          : ord('4'),
            pygame.K_5          : ord('5'),
            pygame.K_6          : ord('6'),
            pygame.K_7          : ord('7'),
            pygame.K_8          : ord('8'),
            pygame.K_9          : ord('9'),
            pygame.K_0          : ord('0'),
            
            pygame.K_ESCAPE     : 0x1b,
            pygame.K_MINUS      : ord('-'),
            pygame.K_EQUALS     : ord('='),
            pygame.K_BACKSPACE  : 0x5f,
            pygame.K_SEMICOLON  : ord(';'),
            pygame.K_BACKSLASH  : ord('\\'),
            pygame.K_COMMA      : ord(','),
            pygame.K_PERIOD     : ord('.'),
            pygame.K_SLASH      : ord('/'),
            pygame.K_SPACE      : ord(' '),
            
            pygame.K_q          : ord('q'),
            pygame.K_w          : ord('w'),
            pygame.K_e          : ord('e'),
            pygame.K_r          : ord('r'),
            pygame.K_t          : ord('t'),
            pygame.K_y          : ord('y'),
            pygame.K_u          : ord('u'),
            pygame.K_i          : ord('i'),
            pygame.K_o          : ord('o'),
            pygame.K_p          : ord('p'),
            pygame.K_a          : ord('a'),
            pygame.K_s          : ord('s'),
            pygame.K_d          : ord('d'),
            pygame.K_f          : ord('f'),
            pygame.K_g          : ord('g'),
            pygame.K_h          : ord('h'),
            pygame.K_j          : ord('j'),
            pygame.K_k          : ord('k'),
            pygame.K_l          : ord('l'),
            pygame.K_z          : ord('z'),
            pygame.K_x          : ord('x'),
            pygame.K_c          : ord('c'),
            pygame.K_v          : ord('v'),
            pygame.K_b          : ord('b'),
            pygame.K_n          : ord('n'),
            pygame.K_m          : ord('m'),
            
            pygame.K_TAB        : 15,
            pygame.K_RETURN     : 0x0d,
            
            pygame.K_BACKQUOTE  : ord('`'),
        }
        
        self._kb_map_upper = {
            pygame.K_1          : ord('!'),
            pygame.K_2          : ord('@'),
            pygame.K_3          : ord('#'),
            pygame.K_4          : ord('$'),
            pygame.K_5          : ord('%'),
            pygame.K_6          : ord('^'),
            pygame.K_7          : ord('&'),
            pygame.K_8          : ord('*'),
            pygame.K_9          : ord('('),
            pygame.K_0          : ord(')'),
            
            pygame.K_ESCAPE     : 0x1b,
            pygame.K_MINUS      : ord('-'),
            pygame.K_EQUALS     : ord('='),
            pygame.K_BACKSPACE  : 0x5f,
            pygame.K_SEMICOLON  : ord(':'),
            pygame.K_BACKSLASH  : ord('|'),
            pygame.K_COMMA      : ord('<'),
            pygame.K_PERIOD     : ord('>'),
            pygame.K_SLASH      : ord('?'),
            pygame.K_SPACE      : ord(' '),
            
            pygame.K_q          : ord('Q'),
            pygame.K_w          : ord('W'),
            pygame.K_e          : ord('E'),
            pygame.K_r          : ord('R'),
            pygame.K_t          : ord('T'),
            pygame.K_y          : ord('Y'),
            pygame.K_u          : ord('U'),
            pygame.K_i          : ord('I'),
            pygame.K_o          : ord('O'),
            pygame.K_p          : ord('P'),
            pygame.K_a          : ord('A'),
            pygame.K_s          : ord('S'),
            pygame.K_d          : ord('D'),
            pygame.K_f          : ord('F'),
            pygame.K_g          : ord('G'),
            pygame.K_h          : ord('H'),
            pygame.K_j          : ord('J'),
            pygame.K_k          : ord('K'),
            pygame.K_l          : ord('L'),
            pygame.K_z          : ord('Z'),
            pygame.K_x          : ord('X'),
            pygame.K_c          : ord('C'),
            pygame.K_v          : ord('V'),
            pygame.K_b          : ord('B'),
            pygame.K_n          : ord('N'),
            pygame.K_m          : ord('M'),
            
            pygame.K_TAB        : 15,
            pygame.K_RETURN     : 0x0d,
            
            pygame.K_BACKQUOTE  : ord('~'),
        }

    def run(self):

        cheight = 24
        font = pygame.freetype.SysFont('Courier', cheight)
        frect = font.get_rect("X")
        cwidth = frect[2]

        swidth = cwidth * 40
        sheight = cheight * 24
        
        ccol= 0
        cline = 0

        screen = pygame.display.set_mode((swidth, sheight))
        screen.fill(self._cblack)
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_LSHIFT) or (event.key == pygame.K_RSHIFT):
                        self._kbShift = True
                        continue
                    if self._kbShift:
                        kmap = self._kb_map_upper
                    else:
                        kmap = self._kb_map_lower
                    if event.key in kmap:
                        self._kbData[0] = kmap[event.key]
                        self._kbSock.sendto(self._kbData, self._kbAddr)
                        time.sleep(0)
                elif event.type == pygame.KEYUP:
                    if (event.key == pygame.K_LSHIFT) or (event.key == pygame.K_RSHIFT):
                        self._kbShift = False
                elif event.type == pygame.QUIT:
                    sys.exit()
                    
            c = self._port._buf[0]
            if c & 0x80:
                c &= 0x7f
                if c == 0x0d:
                    ccol = 0
                    cline += 1
                elif c == 0x1b:
                    pass
                else:
                    self._vram[ccol + (cline * 40)] = c
                    ccol += 1
                    if ccol == 40:
                        ccol = 0
                        cline += 1
                self._port._buf[0] = c
                    
            buf = self._vram
            y = 0
            p = 0
            while p < 960:
                s = ''
                for c in buf[p:p+40]:
                    s += chr(c)
                screen.fill(self._cblack, (0, y, swidth, cheight))
                rect = font.render_to(screen, (0,y), s, self._cgreen)
                y += cheight
                p += 40
            p = 0
            y = 0
            
            pygame.display.flip()
            time.sleep(0.01)
            
    

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("port", type=int, help="UDP port")
    args = parser.parse_args()

    pygame.init()
    app = APPLECON_App(args)
    app.run()

        
        
    
