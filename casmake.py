
    
from argparse import ArgumentParser

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("hex_name", type=str, help="hex file name")
    parser.add_argument("cas_name", type=str, help="cassette file name")
    parser.add_argument("start_addr", type=str, help="image start address (hex)")
    parser.add_argument("end_addr", type=str, help="image end address (hex)")
    args = parser.parse_args()

    hexName = args.hex_name
    casName = args.cas_name
    startAddr = int(args.start_addr, 16)
    endAddr = int(args.end_addr, 16)

    buf = [0x00] * (endAddr - startAddr)

    hexFile = open(hexName, "rt")
    for line in hexFile:
        if line.startswith('S1'):
            n = int(line[2:4], 16) - 3
            offset = int(line[4:8], 16) - startAddr
            for i in range(n):
                buf[offset+i] = int(line[8+(i*2):10+(i*2)], 16)
    hexFile.close()

    buf.reverse()

    casFile = open(casName, "wb")
    casFile.write(bytes(buf))
    casFile.close()
    
    

    
