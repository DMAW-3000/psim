
import socket

from argparse import ArgumentParser

if __name__ == '__main__':
    
    parser = ArgumentParser()
    parser.add_argument("new_disk", type=str, help="new disk file name")
    parser.add_argument("port", type=int, help="changer port number")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    laddr = ('127.0.0.1', args.port + 1)
    
    buf = bytearray(args.new_disk, encoding = "utf8")
    sock.sendto(buf, laddr)
    
    sock.close()
