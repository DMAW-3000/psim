
from dev.fdsk import create_disk, FloppyDisk
from dev.disk import sys_map

import os
import struct
import time
from argparse import ArgumentParser


def zbuf(b):
    for n in range(len(b)):
        b[n] = 0x00
    
def hex_to_sec(dsk, track, sec, fileName):
    xf = open(fileName, 'rt')
    byte = 0
    secSize = dsk.nbytes()
    buf = bytearray(secSize)
    zbuf(buf)
    sc = 0
    
    for line in xf:
        if line.startswith('S1'):
            n = int(line[2:4], 16) - 3
            #print("Format track: %02d sector: %02d byte: %03d" % \
            #      (track, sec, byte))
            for i in range(n):
                buf[byte] = int(line[8+(i*2):10+(i*2)], 16)
                byte += 1
                if byte == secSize:
                    dsk.write_sec(track, sec, buf, 0)
                    zbuf(buf)
                    byte = 0
                    sec += 1
                    sc += 1
                    if sec > dsk.nsector():
                        sec = 1
                        track += 1
                        
    dsk.write_sec(track, sec, buf, 0)
    xf.close()
    return sc + 1
    
def txt_to_sec(dsk, track, sec, fileName, expandCr = True):
    xf = open(fileName, 'rt')
    byte = 0
    secSize = dsk.nbytes()
    buf = bytearray(secSize)
    zbuf(buf)
    bc = 0
    
    for line in xf:
        for i in range(len(line)):
            c = ord(line[i])
            if expandCr and (c == 0x0a):
                buf[byte] = 0x0d
                byte += 1
                bc += 1
                if byte == secSize:
                    dsk.write_sec(track, sec, buf, 0)
                    zbuf(buf)
                    byte = 0
                    sec += 1
                    if sec > dsk.nsector():
                        sec = 1
                        track += 1
            buf[byte] = c
            byte += 1
            bc += 1
            if byte == secSize:
                dsk.write_sec(track, sec, buf, 0)
                zbuf(buf)
                byte = 0
                sec += 1
                if sec > dsk.nsector():
                    sec = 1
                    track += 1
            
    dsk.write_sec(track, sec, buf, 0)
    xf.close()
    return bc    
    
def dos_dir(buf, offset, fname, attr, cluster, size):
    now = time.localtime()
    dw = ((now.tm_year - 1980) << 9) + (now.tm_mon << 5) + now.tm_mday
    tw = (now.tm_hour << 11) + (now.tm_min << 5) + (now.tm_sec >> 1)
    buf[offset+0x00:offset+0x0b] = struct.pack("11s", fname)
    buf[offset+0x0b] = attr
    buf[offset+0x0e] = tw & 0xff
    buf[offset+0x0f] = tw >> 8
    buf[offset+0x10] = dw & 0xff
    buf[offset+0x11] = dw >> 8
    buf[offset+0x12] = dw & 0xff
    buf[offset+0x13] = dw >> 8
    buf[offset+0x16] = tw & 0xff
    buf[offset+0x17] = tw >> 8
    buf[offset+0x18] = dw & 0xff
    buf[offset+0x19] = dw >> 8
    buf[offset+0x1a] = cluster & 0xff
    buf[offset+0x1b] = (cluster >> 8) & 0xff
    buf[offset+0x1c] = size & 0xff
    buf[offset+0x1d] = (size >> 8) & 0xff
    buf[offset+0x1e] = (size >> 16) & 0xff
    buf[offset+0x1f] = (size >> 24) & 0xff
    

def format_pcxt(args, dsk):
    appDir = "app_pcxt"
    secSize = dsk.nbytes()
    buf = bytearray(secSize)
    
    # boot loader to first sector
    if args.boot:
        print("Boot Loader")
        hex_to_sec(dsk, 0, 1, os.path.join(appDir, "pcxtboot.hex"))
    
    # initial FAT (1x2 = 2 sectors)
    print("Initial FAT")
    zbuf(buf)
    buf[0x00] = 0xfe   # FAT ID
    buf[0x01] = 0xff
    buf[0x02] = 0xff
    
    if args.boot:
        buf[0x03] = 0x03   # IO.SYS (2 - 4)
        buf[0x04] = 0x40
        buf[0x05] = 0x00
        buf[0x06] = 0xff
        buf[0x07] = 0x6f   # MSDOS.SYS (5 - 16)
        buf[0x08] = 0x00
        buf[0x09] = 0x07
        buf[0x0a] = 0x80
        buf[0x0b] = 0x00
        buf[0x0c] = 0x09
        buf[0x0d] = 0xa0
        buf[0x0e] = 0x00
        buf[0x0f] = 0x0b
        buf[0x10] = 0xc0
        buf[0x11] = 0x00
        buf[0x12] = 0x0d  
        buf[0x13] = 0xe0
        buf[0x14] = 0x00
        buf[0x15] = 0x0f
        buf[0x16] = 0x00  
        buf[0x17] = 0x01
        buf[0x18] = 0xff
        buf[0x19] = 0x2f  # COMMAND.COM (17 - 26)
        buf[0x1a] = 0x01
        buf[0x1b] = 0x13
        buf[0x1c] = 0x40
        buf[0x1d] = 0x01
        buf[0x1e] = 0x15
        buf[0x1f] = 0x60
        buf[0x20] = 0x01
        buf[0x21] = 0x17
        buf[0x22] = 0x80
        buf[0x23] = 0x01
        buf[0x24] = 0x19
        buf[0x25] = 0xa0
        buf[0x26] = 0x01
        buf[0x27] = 0xff # AUTOEXEC.BAT (27)
        buf[0x28] = 0xff
        buf[0x29] = 0xff
        
    dsk.write_sec(0, 2, buf, 0)
    dsk.write_sec(0, 3, buf, 0)
    
    if args.boot:
    
        # IO.SYS file (3 sectors)
        ioCount = hex_to_sec(dsk, 0, 8, os.path.join(appDir, "msio.hex"))
        print("File IO.SYS, %d sectors" % ioCount)
        
        # MSDOS.SYS file (12 sectors)
        dosCount = hex_to_sec(dsk, 1, 3, os.path.join(appDir, "msdos.hex"))
        print("File MSDOS.SYS, %d sectors" % dosCount)
        
        # COMMAND.COM file (10 sectors)
        comCount = hex_to_sec(dsk, 2, 7, os.path.join(appDir, "mscmd.hex"))
        print("File COMMAND.COM, %d sectors" % comCount)
        
        # AUTOEXEC.BAT file (1 sector)
        autoCount = txt_to_sec(dsk, 4, 1, os.path.join(appDir, "msauto.txt"))
        print("File AUTOEXEC.BAT, %d bytes" % autoCount)
        
        print("Root Directory")
        
        # root directory (64 entries = 4 sectors)
        zbuf(buf)
       
        dos_dir(buf, 0x00, b"IO      SYS", 0x07, 2,  3 * secSize)
        dos_dir(buf, 0x20, b"MSDOS   SYS", 0x07, 5,  12 * secSize)
        dos_dir(buf, 0x40, b"COMMAND COM", 0x01, 17, 10 * secSize)
        dos_dir(buf, 0x60, b"AUTNEXECBAT", 0x00, 27, autoCount)
    
        dsk.write_sec(0, 4, buf, 0)
    
    
def cpm_dir(buf, offset, fname, clusters, size):
    buf[offset+0x01:offset+0x0c] = struct.pack("11s", fname)
    buf[offset+0x0f] = size
    i = 0
    for c in clusters:
        buf[offset+0x10+i] = c
        i += 1
    
def format_mds80(args, dsk):
    appDir = "app_mds80"
    secSize = dsk.nbytes()
    buf = bytearray(secSize)
        
    if args.boot:
    
        # CCP command processor (16 sectors)
        cCount = hex_to_sec(dsk, 0, 2, os.path.join(appDir, "ccp.hex"))
        print("File ccp.hex, %d sectors" % cCount)
        
        # BDOS services (35 sectors)
        bCount = hex_to_sec(dsk, 0, 18, os.path.join(appDir, "bdos.hex"))
        print("File bdos.hex, %d sectors" % bCount)
       
    
    # root (and only) directory (64 entries = 16 sectors)
    
    print("Root directory")
    zbuf(buf)
        
    buf[0]  = 0xe5
    buf[32] = 0xe5
    buf[64] = 0xe5
    buf[96] = 0xe5
    
    for sec in range(1, 17):
        dsk.write_sec(2, sec, buf, 0)
        
    if args.boot:
        
        zbuf(buf)
    
        # DUMP.COM (1 cluster)
        cpm_dir(buf, 0x00, b"DUMP    COM", (2,), 3)
        
        # LOADTAP.COM (2 clusters)
        cpm_dir(buf, 0x20, b"LOADTAP COM", (3,4), 15)
        
        buf[64] = 0xe5
        buf[96] = 0xe5
        
        dsk.write_sec(2, 1, buf, 0) 
        
        dCount = hex_to_sec(dsk, 2, 17, os.path.join(appDir, "cdump.hex"))
        print("File cdump.hex, %d sectors" % dCount)
        
        lCount = hex_to_sec(dsk, 2, 25, os.path.join(appDir, "loadtap.hex"))
        print("File loadtap.hex, %d sectors" % lCount)
    

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("-b", "--boot", action="store_true")
    parser.add_argument("system", type=str, help="system type",
                        choices = sys_map.keys())
    parser.add_argument("name", type=str, help="data store file name")
    args = parser.parse_args()
    
    # create empty disk
    
    create_disk(*sys_map[args.system], args.name)
    
    dsk = FloppyDisk(*sys_map[args.system], args.name)
    if args.system == "pcxt":
        format_pcxt(args, dsk)
    elif args.system == "mds80":
        format_mds80(args, dsk)
       
    
    
    
    

    