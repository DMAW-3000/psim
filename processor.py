
import time

class Processor(object):
    """
    Base processor class
    """

    def __init__(self, clkMod, clkOut):
        self.hlt = False
        self.brk = False
        self.ivec = None
        self._clkmod = clkMod
        self._clkout = clkOut
        self._brklist = set()

    def halt(self):
        self.hlt = True

    def halted(self):
        return self.hlt
        
    def reset(self):
        self.ivec = None
        self._reset()

    def add_break(self, addr):
        self._brklist.add(addr)

    def intr_req(self, vec):
        while self.ivec is not None:
            if self.halted():
                return
            time.sleep(0)
        self.ivec = vec

    def run(self):
        try:
            self.reset()
            self._run_loop()
        except Exception:
            self.halt()
            raise
          
    def _run_loop(self):
        blist = self._brklist
        cmod = self._clkmod
        ic = 0
        while True:
            if len(blist) > 0:
                self.brk = self._check_break(blist)
            while (not self.hlt) and (not self.brk):
                if self.ivec is not None:
                    self._intr()
                self._step()
                ic += 1
                if ic == cmod:
                    if self._clkout is not None:
                        self._clkout()
                    ic = 0
                if len(blist) > 0:
                    self.brk = self._check_break(blist)
            if self.hlt:
                print("HALT")
                self._print_state()
                return
            while True:
                self._print_state()
                print("BREAK")
                c = input('>>')
                if c == 'c':
                    self.brk = False
                    break
                elif c == 's':
                    self._step()
                elif c == '0':
                    print("LOG OFF")
                    self._disable_log()
                elif c == '1':
                    print("LOG ON")
                    self._enable_log()
                elif c == 'r':
                    print("RESET")
                    self.reset()
                elif c == 'q':
                    print("QUIT")
                    self.halt()
                    return

