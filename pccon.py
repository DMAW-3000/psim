
import pygame
import sys
import time
import socket
from multiprocessing import shared_memory
from argparse import ArgumentParser

class PCCON_App(object):

    def __init__(self, args):
    
        self._kbSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._kbAddr = ('127.0.0.1', args.port)
        self._kbData = bytearray(1)
        
        self._vram = shared_memory.SharedMemory("VMEM_MDA", True, 4096)
        c = ord(' ')
        for n in range(self._vram.size):
            self._vram.buf[n] = c
            
        self._vreg = shared_memory.SharedMemory("VREG_6845", True, 256)
        for n in range(self._vreg.size):
            self._vreg.buf[n] = 0x00
            
        self._cblack = pygame.Color(0, 0, 0)
        self._cgreen = pygame.Color(0, 255, 0)
        self._cred   = pygame.Color(255, 0, 0)
        
        self._kb_map = {
            pygame.K_1          : 2,
            pygame.K_2          : 3,
            pygame.K_3          : 4,
            pygame.K_4          : 5,
            pygame.K_5          : 6,
            pygame.K_6          : 7,
            pygame.K_7          : 8,
            pygame.K_8          : 9,
            pygame.K_9          : 10,
            pygame.K_0          : 11,
            
            pygame.K_ESCAPE     : 1,
            pygame.K_MINUS      : 12,
            pygame.K_EQUALS     : 13,
            pygame.K_BACKSPACE  : 14,
            pygame.K_SEMICOLON  : 39,
            pygame.K_BACKSLASH  : 43,
            pygame.K_COMMA      : 51,
            pygame.K_PERIOD     : 52,
            pygame.K_SLASH      : 53,
            pygame.K_SPACE      : 57,
            pygame.K_HOME       : 71,
            pygame.K_PAGEUP     : 73,
            pygame.K_END        : 79,
            pygame.K_PAGEDOWN   : 81,
            pygame.K_INSERT     : 82,
            pygame.K_DELETE     : 83,
            
            pygame.K_q          : 16,
            pygame.K_w          : 17,
            pygame.K_e          : 18,
            pygame.K_r          : 19,
            pygame.K_t          : 20,
            pygame.K_y          : 21,
            pygame.K_u          : 22,
            pygame.K_i          : 23,
            pygame.K_o          : 24,
            pygame.K_p          : 25,
            pygame.K_a          : 30,
            pygame.K_s          : 31,
            pygame.K_d          : 32,
            pygame.K_f          : 33,
            pygame.K_g          : 34,
            pygame.K_h          : 35,
            pygame.K_j          : 36,
            pygame.K_k          : 37,
            pygame.K_l          : 38,
            pygame.K_z          : 44,
            pygame.K_x          : 45,
            pygame.K_c          : 46,
            pygame.K_v          : 47,
            pygame.K_b          : 48,
            pygame.K_n          : 49,
            pygame.K_m          : 50,
            
            pygame.K_TAB        : 15,
            pygame.K_RETURN     : 28,
            pygame.K_LCTRL      : 29,
            pygame.K_RCTRL      : 29,
            pygame.K_LSHIFT     : 42,
            pygame.K_RSHIFT     : 54,
            pygame.K_LALT       : 56,
            pygame.K_RALT       : 56,
            pygame.K_CAPSLOCK   : 58,
            pygame.K_NUMLOCK    : 69,
            
            pygame.K_BACKQUOTE  : 41,
        }

    def run(self):

        cheight = 24
        font = pygame.freetype.SysFont('Courier', cheight)
        frect = font.get_rect("X")
        cwidth = frect[2]

        swidth = cwidth * 80
        sheight = cheight * 25

        screen = pygame.display.set_mode((swidth, sheight))
        screen.fill(self._cblack)
        
        while True:
            for event in pygame.event.get():
                if (event.type == pygame.KEYDOWN) or \
                   (event.type == pygame.KEYUP):
                    if event.key in self._kb_map:
                        x = self._kb_map[event.key]
                        if event.type == pygame.KEYUP:
                            x |= 0x80
                        self._kbData[0] = x
                        self._kbSock.sendto(self._kbData, self._kbAddr)
                        time.sleep(0)
                elif event.type == pygame.QUIT:
                    sys.exit()
            buf = bytearray(self._vram.buf)
            y = 0
            p = 0
            while p < 4000:
                s = ''
                for c in buf[p:p+160:2]:
                    s += chr(c)
                screen.fill(self._cblack, (0, y, swidth, cheight))
                rect = font.render_to(screen, (0,y), s, self._cgreen)
                y += cheight
                p += 160
            p = 0
            y = 0
            pygame.display.flip()
            time.sleep(0.01)
            
    

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("port", type=int, help="UDP port")
    args = parser.parse_args()

    pygame.init()
    app = PCCON_App(args)
    app.run()

        
        
    
