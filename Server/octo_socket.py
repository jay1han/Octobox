import fcntl, os

SOCK_FILE  = '/usr/share/octobox/socket'

class Socket:
   def __init__(self):
      self._lock = None
   
   def lock(self):
      self._lock = open(SOCK_FILE, 'r+')
      fcntl.lockf(self._lock, fcntl.LOCK_EX)

   def free(self, erase=False):
      self._lock.close()
      self._lock = None
      if erase:
         os.truncate(SOCK_FILE, 0)

   def read(self):
      self.lock()
      event = self._lock.read().strip()
    
      self.free(erase=True)
      return event

   def write(self, event):
      self.lock()
      print(event, file=self._lock)
      self.free()
