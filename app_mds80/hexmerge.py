
import sys


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print("hexmerge.py <src1> <src2> ... <srcN> <tgt>")
        sys.exit(-1)

    nsrc = len(sys.argv) - 2
    srcFiles = sys.argv[1:-1]
    tgtFile = sys.argv[-1]

    tf = open(tgtFile, 'wt')

    for s in srcFiles:
        sf = open(s, 'rt')
        print("Input: %s" % s)
        for line in sf.readlines():
            if line.startswith('S1'):
                tf.write(line)
        sf.close()

    tf.close()
    
            
            
        
    
