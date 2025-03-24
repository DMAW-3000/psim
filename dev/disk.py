
import os
import socket

sys_map = {
        "pcxt"  : (1, 40,  8, 512),
        "mds80" : (1, 73, 26, 128)
}


class Disk(object):
    
    def __init__(self, nhead, ntrack, nsector, nbytes, datFile):
        self._nhead = int(nhead)
        self._ntrack = int(ntrack)
        self._nsector = int(nsector)
        self._nbytes = int(nbytes)
        self._head_size = (self._ntrack * self._nsector * self._nbytes)
        if os.path.exists(datFile):
            self._file = open(datFile, "r+b", 0)
        else:
            self._file = open(datFile, "wb")
            
    def nhead(self):
        return self._nhead
        
    def ntrack(self):
        return self._ntrack
        
    def nsector(self):
        return self._nsector
        
    def nbytes(self):
        return self._nbytes
            
    def create(self):
        buf = bytearray(self._nbytes)
        for n in range(self._nbytes):
            buf[n] = 0x00
        for head in range(self._nhead):
            for track in range(self._ntrack):
                for sector in range(self._nsector):
                    self._file.write(buf)
        self._file.close()

    def read_sec(self, track, sector, head = 0):
        sector -= 1
        if (track >= self._ntrack) or \
           (sector < 0) or \
           (sector >= self._nsector) or \
           (head >= self._nhead):
            raise RuntimeError("bad disk read: %d %d" % (track, sector + 1))
        offset = ((track * self._nsector) + sector) * self._nbytes
        offset += (self._head_size * head)
        self._file.seek(offset)
        print("fdsk: read %d %d %d %d" % (head, track, sector + 1, offset))
        return self._file.read(self._nbytes)

    def write_sec(self, track, sector, data, head = 0):
        sector -= 1
        if (track >= self._ntrack) or \
           (sector < 0) or \
           (sector >= self._nsector) or \
           (head >= self._nhead):
                raise RuntimeError("bad disk write: %d %d" % (track, sector + 1))
        offset = ((track * self._nsector) + sector) * self._nbytes
        offset += (self._head_size * head)
        self._file.seek(offset)
        self._file.write(data)
        print("fdsk: write %d %d %d %d" % (head, track, sector + 1, offset))


class DiskChanger(object):

    def __init__(self, port):
        self._rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rx_sock.bind(('', port + 1))
        self._rx_sock.settimeout(2.0)
        
    def recv(self):
        return str(self._rx_sock.recvfrom(32)[0], encoding = "utf8")
                