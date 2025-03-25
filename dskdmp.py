
from dev.fdsk import create_disk, FloppyDisk
from dev.disk import sys_map

import os
from argparse import ArgumentParser



if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("system", type=str, help="system type",
                        choices = sys_map.keys())
    parser.add_argument("name", type=str, help="data store file name")
    parser.add_argument("track", type=int, help="disk track")
    parser.add_argument("sector", type=int, help="track sector")
    args = parser.parse_args()
    
    dsk = FloppyDisk(*sys_map[args.system], args.name)
    
    buf = dsk.read_sec(args.track, args.sector, 0)
       
    for i in range(dsk.nbytes() // 16):
        for j in range(16):
            print("%02x " % buf[(i*16)+j], end='')
        print()
        
    
    
    

    