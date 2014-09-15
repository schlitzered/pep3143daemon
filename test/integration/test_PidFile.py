__author__ = 'schlitzer'

from unittest import TestCase
import pep3143daemon.pidfile
import _io


class TestPidFileIntegration(TestCase):
    def setUp(self):
        self.pidfile = "integration_pidfile.pid"

    def test___init__(self):
        pidfile = pep3143daemon.pidfile.PidFile(self.pidfile)
        self.assertIsNone(pidfile.pidfile)
        self.assertEqual(pidfile._pidfile, self.pidfile)

    def test_acquire(self):
        pidfile = pep3143daemon.pidfile.PidFile(self.pidfile)
        pidfile.acquire()
        self.assertIsInstance(pidfile.pidfile, _io.TextIOWrapper)
        self.assertEqual(pidfile.pidfile.name, self.pidfile)
        self.assertFalse(pidfile.pidfile.closed)
        pidfile.release()

    def test_release(self):
        pidfile = pep3143daemon.pidfile.PidFile(self.pidfile)
        pidfile.acquire()
        pidfile.release()
        self.assertTrue(pidfile.pidfile.closed)

    def test_context(self):
        with pep3143daemon.pidfile.PidFile(self.pidfile) as pidfile:
            self.assertIsInstance(pidfile.pidfile, _io.TextIOWrapper)
            self.assertEqual(pidfile.pidfile.name, self.pidfile)
            self.assertFalse(pidfile.pidfile.closed)
        self.assertTrue(pidfile.pidfile.closed)