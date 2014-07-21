__author__ = 'schlitzer'

from unittest import TestCase
from unittest.mock import Mock, MagicMock, PropertyMock, call, patch
import pep3143daemon.Daemon
import errno
import sys


class TestDaemonContextUnit(TestCase):
    def setUp(self):
        parentisinetpatcher = patch('pep3143daemon.Daemon.parentisinit', autospeck=True)
        self.parentisinet_mock = parentisinetpatcher.start()

        parentisinitpatcher = patch('pep3143daemon.Daemon.parentisinet', autospeck=True)
        self.parentisinit_mock = parentisinitpatcher.start()

        defaultsignalmappatcher = patch('pep3143daemon.Daemon.defaultsignalmap', autospeck=True)
        self.default_signal_map_mock = defaultsignalmappatcher.start()

        detachrequiredpatcher = patch('pep3143daemon.Daemon.detachrequired', autospeck=True)
        self.detachrequiredpatcher_mock = detachrequiredpatcher.start()

        ospatcher = patch('pep3143daemon.Daemon.os', autospeck=True)
        self.os_mock = ospatcher.start()
        self.os_mock.getuid.return_value = 12345
        self.os_mock.getgid.return_value = 54321

        resourcepatcher = patch('pep3143daemon.Daemon.resource', autospeck = True)
        self.resource_mock = resourcepatcher.start()
        self.resource_mock.RLIMIT_NOFILE = 2048
        self.resource_mock.RLIM_INFINITY = True

        signalpatcher = patch('pep3143daemon.Daemon.signal', autospeck=True)
        self.signal_mock = signalpatcher.start()
        self.signal_mock.SIGTERM.return_value=15

        socketpatcher = patch('pep3143daemon.Daemon.socket', autospeck=True)
        self.socket_mock = socketpatcher.start()

        syspatcher = patch('pep3143daemon.Daemon.sys', autospeck=False)
        self.sys_mock = syspatcher.start()

        self.addCleanup(patch.stopall)

        self.daemoncontext = pep3143daemon.Daemon.DaemonContext()
        self.mockdaemoncontext = Mock()

# Test DaemonContext.__init__()
    def test___init__defaultargs(self):
        pep3143daemon.Daemon.DaemonContext.__init__(self.mockdaemoncontext)
        self.assertIsNone(self.mockdaemoncontext.files_preserve)
        self.assertIsNone(self.mockdaemoncontext.chroot_directory)
        self.assertEqual(self.mockdaemoncontext.working_directory, '/')
        self.assertEqual(self.mockdaemoncontext.umask, 0)
        self.assertIsNone(self.mockdaemoncontext.pidfile)
        detach_required = pep3143daemon.Daemon.detachrequired()
        self.assertEqual(self.mockdaemoncontext.detach_process, detach_required)
        signal_map = pep3143daemon.Daemon.defaultsignalmap()
        self.assertEqual(self.mockdaemoncontext.signal_map, signal_map)
        self.assertEqual(self.mockdaemoncontext.uid, self.os_mock.getuid())
        self.os_mock.getuid.assert_called_with()
        self.assertEqual(self.mockdaemoncontext.gid, self.os_mock.getgid())
        self.os_mock.getgid.assert_called_with()
        self.assertTrue(self.mockdaemoncontext.prevent_core)
        self.assertIsNone(self.mockdaemoncontext.stdin)
        self.assertIsNone(self.mockdaemoncontext.stdout)
        self.assertIsNone(self.mockdaemoncontext.stderr)
        self.assertFalse(self.mockdaemoncontext._is_open)

    def test___init__customargs(self):
        files_preserve = Mock()
        chroot_directory = Mock()
        working_directory = Mock()
        umask = Mock()
        pidfile = Mock()
        detach_process = Mock()
        signal_map = Mock()
        uid = Mock()
        gid = Mock()
        prevent_core = Mock()
        stdin = Mock()
        stdout = Mock()
        stderr = Mock()

        pep3143daemon.Daemon.DaemonContext.__init__(
            self.mockdaemoncontext,
            files_preserve=files_preserve,
            chroot_directory=chroot_directory,
            working_directory=working_directory,
            umask=umask,
            pidfile=pidfile,
            detach_process=detach_process,
            signal_map=signal_map,
            uid=uid,
            gid=gid,
            prevent_core=prevent_core,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr)

        self.assertEqual(self.mockdaemoncontext.files_preserve, files_preserve)
        self.assertEqual(self.mockdaemoncontext.chroot_directory, chroot_directory)
        self.assertEqual(self.mockdaemoncontext.working_directory, working_directory)
        self.assertEqual(self.mockdaemoncontext.umask, umask)
        self.assertEqual(self.mockdaemoncontext.pidfile, pidfile)
        self.assertEqual(self.mockdaemoncontext.detach_process, detach_process)
        self.assertEqual(self.mockdaemoncontext.signal_map, signal_map)
        self.assertEqual(self.mockdaemoncontext.uid, uid)
        self.assertEqual(self.mockdaemoncontext.gid, gid)
        self.assertEqual(self.mockdaemoncontext.prevent_core, prevent_core)
        self.assertEqual(self.mockdaemoncontext.stdin, stdin)
        self.assertEqual(self.mockdaemoncontext.stdout, stdout)
        self.assertEqual(self.mockdaemoncontext.stderr, stderr)

    def test___init__chroot_substring_of_workdir(self):
        pep3143daemon.Daemon.DaemonContext.__init__(
            self.mockdaemoncontext,
            working_directory='/foo/bar/baz',
            chroot_directory='/foo/bar')
        self.assertEqual(self.mockdaemoncontext.working_directory, '/foo/bar/baz')

    def test___init__chroot_not_substring_of_workdir(self):
        pep3143daemon.Daemon.DaemonContext.__init__(
            self.mockdaemoncontext,
            working_directory='/baz',
            chroot_directory='/foo/bar')
        self.assertEqual(self.mockdaemoncontext.working_directory, '/foo/bar/baz')

# Test DaemonContext._exclude_filenos
    def test_exclude_filenos(self):
        file1 = Mock()
        file1.fileno.return_value = 1
        file2 = Mock()
        file2.fileno.return_value = 16
        self.daemoncontext.stdin = file1
        self.daemoncontext.files_preserve = [file2, 2, 1, 4, 15]
        result = self.daemoncontext._files_preserve
        self.assertEqual(result, set((1, 2, 4 ,15, 16)))

# Test DaemonContext._get_signal_handler()
    def test__get_signal_handler_None(self):
        result = pep3143daemon.Daemon.DaemonContext._get_signal_handler(
            self.mockdaemoncontext,
            None)
        self.assertEqual(result, self.signal_mock.SIG_IGN)

    def test__get_signal_handler_attribute(self):
        result = pep3143daemon.Daemon.DaemonContext._get_signal_handler(
            self.mockdaemoncontext,
            'terminate')
        self.assertEqual(result, self.mockdaemoncontext.terminate)

    def test__get_signal_handler_other(self):
        other = Mock()
        result = pep3143daemon.Daemon.DaemonContext._get_signal_handler(
            self.mockdaemoncontext,
            other)
        self.assertEqual(result, other)

# Test DaemonContext._is_open_()
    def test__is_open_get_equals__is_open(self):
        self.assertEqual(self.daemoncontext.is_open, self.daemoncontext._is_open)

    def test__is_open_get_equals_false(self):
        self.assertFalse(self.daemoncontext.is_open)

    def test__is_open_set_should_fail(self):
        self.assertRaises(AttributeError, setattr, self.daemoncontext, 'is_open', 1)

    def test__is_open_def_should_fail(self):
        self.assertRaises(AttributeError, delattr, self.daemoncontext, 'is_open')


# Test DaemonContext.signal_handler_map
    def test__signal_handler_map(self):
        self.daemoncontext.signal_map = {
            self.signal_mock.SIGTSTP: None,
            self.signal_mock.SIGTTIN: None,
            self.signal_mock.SIGTTOU: None,
            self.signal_mock.SIGTERM: 'terminate'}

        expected = {
            self.signal_mock.SIGTSTP: self.signal_mock.SIG_IGN,
            self.signal_mock.SIGTTIN: self.signal_mock.SIG_IGN,
            self.signal_mock.SIGTTOU: self.signal_mock.SIG_IGN,
            self.signal_mock.SIGTERM: self.daemoncontext.terminate}

        result = self.daemoncontext._signal_handler_map
        self.assertEqual(result, expected)

# Test DaemonContext.open()
    def test_open_first_fork_parent_second_fork_parent(self):
        self.os_mock.fork = MagicMock(side_effect=[123, 1123])
        self.sys_mock.exit.side_effect = SystemExit
        self.daemoncontext.pidfile = Mock()
        self.daemoncontext.signal_map = {
            self.signal_mock.SIGTSTP: None,
            self.signal_mock.SIGTTIN: None,
            self.signal_mock.SIGTTOU: None,
            self.signal_mock.SIGTERM: 'terminate'}

        with self.assertRaises(SystemExit) as err:
            self.daemoncontext.open()

        self.os_mock.assert_has_calls(
            [call.getuid(),
             call.getgid(),
             call.chdir('/'),
             call.setgid(54321),
             call.setuid(12345),
             call.umask(0),
             call.fork()])
        self.resource_mock.assert_has_calls(
            [call.setrlimit(self.resource_mock.RLIMIT_CORE, (0, 0))])

    def test_open_first_fork_child_second_fork_parent(self):
        self.os_mock.fork = MagicMock(side_effect=[0, 1123])
        self.sys_mock.exit.side_effect = SystemExit
        self.daemoncontext.pidfile = Mock()
        self.daemoncontext.signal_map = {
            self.signal_mock.SIGTSTP: None,
            self.signal_mock.SIGTTIN: None,
            self.signal_mock.SIGTTOU: None,
            self.signal_mock.SIGTERM: 'terminate'}

        with self.assertRaises(SystemExit) as err:
            self.daemoncontext.open()

        self.os_mock.assert_has_calls(
            [call.getuid(),
             call.getgid(),
             call.chdir('/'),
             call.setgid(54321),
             call.setuid(12345),
             call.umask(0),
             call.fork(),
             call.setsid(),
             call.fork()])
        self.resource_mock.assert_has_calls(
            [call.setrlimit(self.resource_mock.RLIMIT_CORE, (0, 0))])

    def test_open_first_fork_child_second_fork_child(self):
        self.os_mock.fork = MagicMock(side_effect=[0, 0])
        self.daemoncontext.pidfile = Mock()
        terminate = getattr(self.daemoncontext, 'terminate')
        self.daemoncontext.signal_map = {
            self.signal_mock.SIGTSTP: None,
            self.signal_mock.SIGTTIN: None,
            self.signal_mock.SIGTTOU: None,
            self.signal_mock.SIGTERM: 'terminate'}

        self.daemoncontext.open()

        self.os_mock.assert_has_calls(
            [call.getuid(),
             call.getgid(),
             call.chdir('/'),
             call.setgid(54321),
             call.setuid(12345),
             call.umask(0),
             call.fork(),
             call.setsid(),
             call.fork(),
             call.close(0),
             call.open(self.os_mock.devnull, self.os_mock.O_RDWR),
             call.dup2(self.os_mock.open(), self.sys_mock.stdin.fileno()),
             call.open(self.os_mock.devnull, self.os_mock.O_RDWR),
             call.dup2(self.os_mock.open(), self.sys_mock.stdout.fileno()),
             call.open(self.os_mock.devnull, self.os_mock.O_RDWR),
             call.dup2(self.os_mock.open(), self.sys_mock.stderr.fileno())])
        self.resource_mock.assert_has_calls(
            [call.setrlimit(self.resource_mock.RLIMIT_CORE, (0, 0)),
             call.getrlimit(2048)])
        self.signal_mock.assert_has_calls(
            [call.signal(self.signal_mock.SIGTSTP, self.signal_mock.SIG_IGN),
             call.signal(self.signal_mock.SIGTERM, terminate),
             call.signal(self.signal_mock.SIGTTIN, self.signal_mock.SIG_IGN),
             call.signal(self.signal_mock.SIGTTOU, self.signal_mock.SIG_IGN)], any_order=True)
        self.sys_mock.assert_has_calls(
            [call.stdin.fileno(),
             call.stdout.fileno(),
             call.stderr.fileno(),
             call.stdin.fileno(),
             call.stdout.fileno(),
             call.stderr.fileno()])

    def test_open_first_fork_child_second_fork_child_and_pitfile(self):
        self.os_mock.fork = MagicMock(side_effect=[0, 0])
        self.daemoncontext.pidfile = Mock()
        terminate = getattr(self.daemoncontext, 'terminate')
        self.daemoncontext.signal_map = {
            self.signal_mock.SIGTSTP: None,
            self.signal_mock.SIGTTIN: None,
            self.signal_mock.SIGTTOU: None,
            self.signal_mock.SIGTERM: 'terminate'}

        self.daemoncontext.open()

        self.os_mock.assert_has_calls(
            [call.getuid(),
             call.getgid(),
             call.chdir('/'),
             call.setgid(54321),
             call.setuid(12345),
             call.umask(0),
             call.fork(),
             call.setsid(),
             call.fork(),
             call.close(0),
             call.open(self.os_mock.devnull, self.os_mock.O_RDWR),
             call.dup2(self.os_mock.open(), self.sys_mock.stdin.fileno()),
             call.open(self.os_mock.devnull, self.os_mock.O_RDWR),
             call.dup2(self.os_mock.open(), self.sys_mock.stdout.fileno()),
             call.open(self.os_mock.devnull, self.os_mock.O_RDWR),
             call.dup2(self.os_mock.open(), self.sys_mock.stderr.fileno())])
        self.resource_mock.assert_has_calls(
            [call.setrlimit(self.resource_mock.RLIMIT_CORE, (0, 0)),
             call.getrlimit(2048)])
        self.signal_mock.assert_has_calls(
            [call.signal(self.signal_mock.SIGTSTP, self.signal_mock.SIG_IGN),
             call.signal(self.signal_mock.SIGTERM, terminate),
             call.signal(self.signal_mock.SIGTTIN, self.signal_mock.SIG_IGN),
             call.signal(self.signal_mock.SIGTTOU, self.signal_mock.SIG_IGN)], any_order=True)
        self.sys_mock.assert_has_calls(
            [call.stdin.fileno(),
             call.stdout.fileno(),
             call.stderr.fileno(),
             call.stdin.fileno(),
             call.stdout.fileno(),
             call.stderr.fileno()])
        self.daemoncontext.pidfile.assert_has_calls(
            [call.acquire()]
        )

class TestDaemonHelperUnit(TestCase):
    def setUp(self):
        ospatcher = patch('pep3143daemon.Daemon.os', autospeck=True)
        self.os_mock = ospatcher.start()
        self.os_mock.getuid.return_value = 12345
        self.os_mock.getgid.return_value = 54321

        resourcepatcher = patch('pep3143daemon.Daemon.resource', autospeck=True)
        self.resource_mock = resourcepatcher.start()

        signalpatcher = patch('pep3143daemon.Daemon.signal', autospeck=True)
        self.signal_mock = signalpatcher.start()
        self.signal_mock.SIGTERM.return_value=15

        socketpatcher = patch('pep3143daemon.Daemon.socket', autospeck=True)
        self.socket_mock = socketpatcher.start()

        syspatcher = patch('pep3143daemon.Daemon.sys', autospeck=False)
        self.sys_mock = syspatcher.start()

        self.addCleanup(patch.stopall)

        self.mockdaemoncontext = Mock()

# Test close_filenos()

    def test_close_filenos_maxfd_12(self):
        self.resource_mock.getrlimit.return_value = (12, 12)
        calls = [call.close(0),
                 call.close(3),
                 call.close(5),
                 call.close(6),
                 call.close(7),
                 call.close(8),
                 call.close(10),
                 call.close(11)]
        pep3143daemon.Daemon.close_filenos(set((1,2,4,9)))
        self.os_mock.assert_has_calls(calls)

    def test_close_filenos_maxfd_unlimited(self):
        self.resource_mock.getrlimit.return_value = (12, self.resource_mock.RLIM_INFINITY)
        pep3143daemon.Daemon.close_filenos(set((1,2,4,9)))
        self.assertEqual(self.os_mock.close.call_count, 4092)

# Test default_signal_map()

    def test_default_signal_map(self):
        expected = {
            self.signal_mock.SIGTSTP: None,
            self.signal_mock.SIGTTIN: None,
            self.signal_mock.SIGTTOU: None,
            self.signal_mock.SIGTERM: 'terminate'}
        result = pep3143daemon.Daemon.defaultsignalmap()
        self.assertEqual(result, expected)

    def test_default_signal_map_no_SIGTTOU(self):
        del self.signal_mock.SIGTTOU
        expected = {
            self.signal_mock.SIGTSTP: None,
            self.signal_mock.SIGTTIN: None,
            self.signal_mock.SIGTERM: 'terminate'}
        result = pep3143daemon.Daemon.defaultsignalmap()
        self.assertEqual(result, expected)

# Test parentisinit()

    def test_parentisinit_true(self):
        self.os_mock.getppid.return_value = 1
        self.assertTrue(pep3143daemon.Daemon.parentisinit())

    def test_parentisinit_false(self):
        self.os_mock.getppid.return_value = 12345
        self.assertFalse(pep3143daemon.Daemon.parentisinit())

# Test parentisinet()

    def test_parentisinet_true(self):
        self.sys_mock.__stdin__ = Mock()
        self.assertTrue(pep3143daemon.Daemon.parentisinet())

    def test_parentisinet_true_sockerr(self):
        self.sys_mock.__stdin__ = Mock()
        sock = Mock()
        sock.getsockopt.side_effect = OSError('other socket error')
        self.socket_mock.fromfd.return_value = sock
        self.assertTrue(pep3143daemon.Daemon.parentisinet())

    def test_parentisinet_false_ENOTSOCK(self):
        self.sys_mock.__stdin__ = Mock()
        sock = Mock()
        sock.getsockopt.side_effect = OSError(errno.ENOTSOCK)
        self.socket_mock.fromfd.return_value = sock
        self.assertFalse(pep3143daemon.Daemon.parentisinet())

# test detachrequired()

    def test_detachrequired_false_parentisinet_true(self):
        parentisinetpatcher = patch('pep3143daemon.Daemon.parentisinit', autospeck=True)
        parentisinet_mock = parentisinetpatcher.start()
        parentisinet_mock.return_value = True

        parentisinitpatcher = patch('pep3143daemon.Daemon.parentisinet', autospeck=True)
        parentisinit_mock = parentisinitpatcher.start()
        parentisinit_mock.return_value = False
        self.assertFalse(pep3143daemon.Daemon.detachrequired())

    def test_detachrequired_false_parentisinit_true(self):
        parentisinetpatcher = patch('pep3143daemon.Daemon.parentisinit', autospeck=True)
        parentisinet_mock = parentisinetpatcher.start()
        parentisinet_mock.return_value = False

        parentisinitpatcher = patch('pep3143daemon.Daemon.parentisinet', autospeck=True)
        parentisinit_mock = parentisinitpatcher.start()
        parentisinit_mock.return_value = True
        self.assertFalse(pep3143daemon.Daemon.detachrequired())

    def test_detachrequired_true(self):
        parentisinetpatcher = patch('pep3143daemon.Daemon.parentisinit', autospeck=True)
        parentisinet_mock = parentisinetpatcher.start()
        parentisinet_mock.return_value = False

        parentisinitpatcher = patch('pep3143daemon.Daemon.parentisinet', autospeck=True)
        parentisinit_mock = parentisinitpatcher.start()
        parentisinit_mock.return_value = False
        self.assertTrue(pep3143daemon.Daemon.detachrequired())

# Test redirect_stream()
    def test_redirect_stream_None(self):
        file = Mock()
        file.fileno.return_value = 123
        pep3143daemon.Daemon.redirect_stream(file, None)
        self.os_mock.assert_has_calls(
            [call.open(self.os_mock.devnull, self.os_mock.O_RDWR),
             call.dup2(self.os_mock.open(), 123)])

    def test_redirect_stream_fileno(self):
        file1 = Mock()
        file1.fileno.return_value = 123
        file2 = Mock()
        file2.fileno.return_value = 321
        pep3143daemon.Daemon.redirect_stream(file1, file2)
        self.os_mock.assert_has_calls([call.dup2(321, 123)])
