"""
Simple PidFile Module for a pep3143 daemon implementation

"""
__author__ = 'schlitzer'


import atexit
import fcntl
import os


class PidFile(object):
    """
    PidFile object for PEP 3128 Daemon

    :param pidfile: filename to be used as pidfile, including path
    """

    def __init__(self, pidfile):
        """
        Create a new instance
        """
        self._pidfile = pidfile
        self.pidfile = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            self.release()
            return False
        self.release()
        return True

    def acquire(self):
        """Acquire the pidfile.

        Create the pidfile, lock it, write the pid into it
        and register the release with atexit.


        :raise SystemExit:
        """
        try:
            self.pidfile = open(self._pidfile, "w+")
        except IOError as err:
            raise SystemExit(err)
        try:
            fcntl.flock(self.pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            raise SystemExit('Already running according to ' + self._pidfile)
        self.pidfile.write(str(os.getpid())+'\n')
        self.pidfile.flush()
        atexit.register(self.release)

    def release(self):
        """Release the pidfile.

        Close and delete the Pidfile.


        :raise:
        """
        try:
            self.pidfile.close()
            os.remove(self._pidfile)
        except OSError as err:
            if err.errno != 2:
                raise
