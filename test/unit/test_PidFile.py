__author__ = 'schlitzer'

from unittest import TestCase
from unittest.mock import Mock, call, patch
import pep3143daemon.pidfile


class TestPidFileUnit(TestCase):
    def setUp(self):
        atexitpatcher = patch('pep3143daemon.pidfile.atexit', autospeck=True)
        self.atexit_mock = atexitpatcher.start()

        fcntlpatcher = patch('pep3143daemon.pidfile.fcntl', autospeck=True)
        self.fcntl_mock = fcntlpatcher.start()

        openpatcher = patch('builtins.open', autospeck=True)
        self.open_mock = openpatcher.start()

        ospatcher = patch('pep3143daemon.pidfile.os', autospeck=True)
        self.os_mock = ospatcher.start()
        self.os_mock.getpid.return_value = 12345

        self.addCleanup(patch.stopall)

        self.mockpidfile = Mock()

    def test___init__(self):
        pep3143daemon.pidfile.PidFile.__init__(self.mockpidfile, 'test.pid')
        self.assertIsNone(self.mockpidfile.pidfile)
        self.assertEqual(self.mockpidfile._pidfile, 'test.pid')


    def test_acquire(self):
        self.mockpidfile._pidfile = 'test.pid'
        pep3143daemon.pidfile.PidFile.acquire(self.mockpidfile)

        self.open_mock.assert_called_with('test.pid', 'a')

        self.assertEqual(self.mockpidfile._pidfile, 'test.pid')
        self.fcntl_mock.flock.asert_called_with(
            self.mockpidfile.pidfile.fileno(),
            self.fcntl_mock.LOCK_EX | self.fcntl_mock.LOCK_NB)

        self.os_mock.getpid.assert_called_with()

        self.mockpidfile.pidfile.fileno.assert_has_calls([
            call(),
            call()
        ]
        )
        self.mockpidfile.pidfile.write.assert_called_with(str(self.os_mock.getpid()) + '\n')
        self.mockpidfile.pidfile.flush.assert_called_with()

        self.atexit_mock.register.assert_called_with(self.mockpidfile.release)

    def test_acquire_flock_fail(self):
        self.mockpidfile._pidfile = 'test.pid'
        self.fcntl_mock.flock.side_effect = IOError()
        self.assertRaises(SystemExit, pep3143daemon.pidfile.PidFile.acquire, (self.mockpidfile))

    def test_acquire_open_fail(self):
        self.mockpidfile._pidfile = 'test.pid'
        self.open_mock.side_effect = IOError()
        self.assertRaises(SystemExit, pep3143daemon.pidfile.PidFile.acquire, (self.mockpidfile))

    def test_release(self):
        self.mockpidfile._pidfile = 'test.pid'
        pep3143daemon.pidfile.PidFile.release(self.mockpidfile)

        self.mockpidfile.pidfile.close.assert_called_with()

        self.os_mock.remove.assert_called_with(self.mockpidfile._pidfile)