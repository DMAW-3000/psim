
import pygame
import time
import sys

class Seg(object):

    def __init__(self, img, rect):
        self.img = img
        self.rect = rect

if __name__ == '__main__':

    nseg = int(sys.argv[1])

    pygame.init()
    
    screen = pygame.display.set_mode(((68 * nseg) + 4, 120))
    screen.fill((0,0,0))
    pygame.display.flip()
    time.sleep(1)

    imgArr = []
    rectArr = []

    for n in range(nseg):
        rectArr.append(pygame.Rect(n * 68, 0, 68, 128))
        
    for i in range(10):
        imgArr.append(pygame.image.load("..\..\Pictures\seven-segment_%d.bmp" % i))

    c = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break
        for n in range(nseg):
            rect = rectArr[n]
            screen.fill((0,0,0), rect)
            screen.blit(imgArr[c], rect.move(4, 0))
        c += 1
        if c == 10:
            c = 0
        pygame.display.flip()
        time.sleep(1)
        
        
    
