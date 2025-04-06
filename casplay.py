
import sys
import socket
import time

from argparse import ArgumentParser

if __name__ == '__main__':
    
    parser = ArgumentParser()
    parser.add_argument("name", type=str, help="cassette file name")
    parser.add_argument("port", type=int, help="serial port number")
    parser.add_argument("-t", "--trailer", type=str, action="store",
                        help="trailing character (hex)")
    parser.add_argument("-x", "--xonoff", action="store_true",
                        help="use XON/XOFF flow control")
    args = parser.parse_args()
    
    casName = args.name
    port = args.port
    
    if args.trailer is not None:
        trailer = int(args.trailer, 16) & 0xff
    else:
        trailer = None

    casFile = open(casName, "rb")
    writeSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    readSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    readSock.bind(('', port))
    readSock.setblocking(False)
    laddr = ('127.0.0.1', port + 1)
    
    cBuf = bytearray(1)
    count = 0
    xon = not args.xonoff
    
    while True:
        # check the input socket for flow control
        try:
            (buf, iaddr) = readSock.recvfrom(1024)
            if len(buf) > 0:
                c = int(buf[0])
                if c == 0x12:
                    xon = True
                elif c == 0x14:
                    xon = False
        except BlockingIOError:
            pass
            
        if xon:
            # get the next byte from the input file
            # exit on end-of-file
            buf = casFile.read(1)
            if not len(buf):
                break
                
            # send byte to receiver
            writeSock.sendto(buf, laddr)
            
            # update display
            if not (count % 128):
                print("*", end = '')
                sys.stdout.flush()
            count += 1
        
        # pause
        time.sleep(0.05)
      
    # add optional trailer byte
    if trailer is not None:
        cBuf[0] = trailer
        sock.sendto(bytes(cBuf), laddr)

    casFile.close()
    writeSock.close()
    readSock.close()
