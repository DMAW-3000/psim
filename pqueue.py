"""
Mutithreaded queue with timeout
"""

import collections
import threading

class PQueue(object):

    def __init__(self, size):
        """
        Create a queue of size max items
        """
        self._q = collections.deque(maxlen=size)
        self._s = threading.Semaphore(0)
        
    def full(self):
        """
        Return true if queue is full
        """
        return len(self._q) == self._q.maxlen
        
    def empty(self):
        """
        Return true if queue is empty
        """
        return len(self._q) == 0
     
    def put(self, value):
        """
        Add a item to the queue
        
        XXX Needs to handle overflow case
        """
        self._q.appendleft(value)
        self._s.release()
        
    def get(self, timeout):
        """
        Get an item from the queue.  Reader will block until
        item is available or timeout seconds expires.
        Returns the item, or None if there was a timeout.
        
        XXX Needs to handle case of None value for timeout
        """
        self._s.acquire(True, timeout)
        try:
            value = self._q.pop()
        except IndexError:
            value = None
        return value
        
        
if __name__ == '__main__':

    import time

    q = PQueue(5)
    
    def reader():
        while True:
            x = q.get(1.0)
            if x is None:
                print("timeout")
            elif x == 100:
                return
            else:
                print(x)
    
    threading.Thread(target=reader).start()
    
    for n in range(100):
        while q.full():
            time.sleep(0)
        q.put(n)
        
    time.sleep(5.0)
        
    q.put(100)
        