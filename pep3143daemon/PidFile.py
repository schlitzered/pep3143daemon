__author__ = 'schlitzer'

import atexit
import fcntl
import os


class PidFile(object):
    def __init__(self, pidfile):
        self._pidfile = pidfile
        self.pidfile = None

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            self.release()
            return False
        self.release()
        return True

    def acquire(self):
        self.pidfile = open(self._pidfile, "w+")
        try:
            fcntl.flock(self.pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            raise SystemExit("Already running according to " + self._pidfile)
        self.pidfile.write(str(os.getpid())+'\n')
        self.pidfile.flush()
        atexit.register(self.release)

    def release(self):
        try:
            self.pidfile.close()
            os.remove(self._pidfile)
        except IOError as err:
            if err.errno != 9:
                raise
        except OSError as err:
            if err.errno != 2:
                raise