
import argparse

class AppParser(object):

    def __init__(self, ioFlag = True):
        self._parser = argparse.ArgumentParser()
        self._parser.add_argument('-m', '--mem_log', action="store_true",
                                  help="create memory space log")
        if ioFlag:
            self._parser.add_argument('-i', '--io_log', action="store_true",
                                      help="create I/O space log")
        self._parser.add_argument('-d', '--debug', action="store_true",
                                  help="run in debug mode")
        self._parser.add_argument('breaks', metavar='breakN', type=str, nargs="*",
                                  help="list of breakpoint addresses")
        
    def parse(self):
        return self._parser.parse_args()