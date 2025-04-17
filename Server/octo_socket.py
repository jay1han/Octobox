import fcntl, os

SOCK_FILE  = '/usr/share/octobox/socket'

class Socket:
   def __init__(self):
      self.lock = None
   
   def lock(self):
      self.lock = open(SOCK_FILE, 'r+')
      fcntl.lockf(self.lock, fcntl.LOCK_EX)

   def free(self, erase=False):
      self.lock.close()
      self.lock = None
      if erase:
         os.truncate(SOCK_FILE, 0)

   def read(self):
      self.lock()
      event = self.lock.read().strip()
    
      self.free(erase=True)
      return event

   def write(self, event):
      self.lock()
      self.lock.print(event)
      self.free()
