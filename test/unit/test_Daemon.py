__author__ = 'schlitzer'

from unittest import TestCase
try:
    from unittest.mock import Mock, MagicMock, call, patch
except ImportError:
    from mock import Mock, MagicMock, call, patch

import pep3143daemon.daemon
import errno


class LowLevelExit(SystemExit):
    pass


class TestDaemonContextUnit(TestCase):
    def setUp(self):
        parent_is_inetpatcher = patch('pep3143daemon.daemon.parent_is_init', autospeck=True)
        self.parent_is_inet_mock = parent_is_inetpatcher.start()

        parent_is_initpatcher = patch('pep3143daemon.daemon.parent_is_inet', autospeck=True)
        self.parent_is_init_mock = parent_is_initpatcher.start()

        default_signal_mappatcher = patch('pep3143daemon.daemon.default_signal_map', autospeck=True)
        self.default_signal_map_mock = default_signal_mappatcher.start()

        detach_requiredpatcher = patch('pep3143daemon.daemon.detach_required', autospeck=True)
        self.detach_requiredpatcher_mock = detach_requiredpatcher.start()

        ospatcher = patch('pep3143daemon.daemon.os', autospeck=True)
        self.os_mock = ospatcher.start()
        self.os_mock.getuid.return_value = 12345
        self.os_mock.getgid.return_value = 54321

        resourcepatcher = patch('pep3143daemon.daemon.resource', autospeck=True)
        self.resource_mock = resourcepatcher.start()
        self.resource_mock.RLIMIT_NOFILE = 2048
        self.resource_mock.RLIM_INFINITY = True

        signalpatcher = patch('pep3143daemon.daemon.signal', autospeck=True)
        self.signal_mock = signalpatcher.start()
        self.signal_mock.SIGTERM.return_value = 15

        socketpatcher = patch('pep3143daemon.daemon.socket', autospeck=True)
        self.socket_mock = socketpatcher.start()

        syspatcher = patch('pep3143daemon.daemon.sys', autospeck=False)
        self.sys_mock = syspatcher.start()

        self.daemoncontext = pep3143daemon.daemon.DaemonContext()

        self.addCleanup(patch.stopall)

# Test DaemonContext.__init__()
    def test___init__defaultargs(self):
        daemon = pep3143daemon.daemon.DaemonContext()
        self.assertIsNone(daemon.files_preserve)
        self.assertIsNone(daemon.chroot_directory)
        self.assertEqual(daemon.working_directory, '/')
        self.assertEqual(daemon.umask, 0)
        self.assertIsNone(daemon.pidfile)
        detach_required = pep3143daemon.daemon.detach_required()
        self.assertEqual(daemon.detach_process, detach_required)
        signal_map = pep3143daemon.daemon.default_signal_map()
        self.assertEqual(daemon.signal_map, signal_map)
        self.assertEqual(daemon.uid, self.os_mock.getuid())
        self.os_mock.getuid.assert_called_with()
        self.assertEqual(daemon.gid, self.os_mock.getgid())
        self.os_mock.getgid.assert_called_with()
        self.assertTrue(daemon.prevent_core)
        self.assertIsNone(daemon.stdin)
        self.assertIsNone(daemon.stdout)
        self.assertIsNone(daemon.stderr)
        self.assertFalse(daemon._is_open)

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

        daemon = pep3143daemon.daemon.DaemonContext(
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

        self.assertEqual(daemon.files_preserve, files_preserve)
        self.assertEqual(daemon.chroot_directory, chroot_directory)
        self.assertEqual(daemon.working_directory, working_directory)
        self.assertEqual(daemon.umask, umask)
        self.assertEqual(daemon.pidfile, pidfile)
        self.assertEqual(daemon.detach_process, detach_process)
        self.assertEqual(daemon.signal_map, signal_map)
        self.assertEqual(daemon.uid, uid)
        self.assertEqual(daemon.gid, gid)
        self.assertEqual(daemon.prevent_core, prevent_core)
        self.assertEqual(daemon.stdin, stdin)
        self.assertEqual(daemon.stdout, stdout)
        self.assertEqual(daemon.stderr, stderr)

    def test___init__chroot_substring_of_workdir(self):
        daemon = pep3143daemon.daemon.DaemonContext(
            working_directory='/foo/bar/baz',
            chroot_directory='/foo/bar')
        self.assertEqual(daemon.working_directory, '/foo/bar/baz')

    def test___init__chroot_not_substring_of_workdir(self):
        daemon = pep3143daemon.daemon.DaemonContext(
            working_directory='/baz',
            chroot_directory='/foo/bar')
        self.assertEqual(daemon.working_directory, '/foo/bar/baz')

# Test DaemonContext._exclude_filenos
    def test_exclude_filenos(self):
        file1 = Mock()
        file1.fileno.return_value = 1
        file2 = Mock()
        file2.fileno.return_value = 16
        self.daemoncontext.stdin = file1
        self.daemoncontext.files_preserve = [file2, 2, 1, 4, 15]
        result = self.daemoncontext._files_preserve
        self.assertEqual(result, set((1, 2, 4, 15, 16)))

# Test DaemonContext._get_signal_handler()
    def test__get_signal_handler_None(self):
        result = pep3143daemon.daemon.DaemonContext._get_signal_handler(
            self.daemoncontext,
            None)
        self.assertEqual(result, self.signal_mock.SIG_IGN)

    def test__get_signal_handler_attribute(self):
        result = pep3143daemon.daemon.DaemonContext._get_signal_handler(
            self.daemoncontext,
            'terminate')
        self.assertEqual(result, self.daemoncontext.terminate)

    def test__get_signal_handler_other(self):
        other = Mock()
        result = pep3143daemon.daemon.DaemonContext._get_signal_handler(
            self.daemoncontext,
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
        self.os_mock._exit.side_effect = LowLevelExit
        self.daemoncontext.pidfile = Mock()
        self.daemoncontext.signal_map = {
            self.signal_mock.SIGTSTP: None,
            self.signal_mock.SIGTTIN: None,
            self.signal_mock.SIGTTOU: None,
            self.signal_mock.SIGTERM: 'terminate'}

        with self.assertRaises(LowLevelExit) as err:
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
        self.os_mock._exit.side_effect = LowLevelExit
        self.daemoncontext.pidfile = Mock()
        self.daemoncontext.signal_map = {
            self.signal_mock.SIGTSTP: None,
            self.signal_mock.SIGTTIN: None,
            self.signal_mock.SIGTTOU: None,
            self.signal_mock.SIGTERM: 'terminate'}

        with self.assertRaises(LowLevelExit) as err:
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
        ospatcher = patch('pep3143daemon.daemon.os', autospeck=True)
        self.os_mock = ospatcher.start()
        self.os_mock.getuid.return_value = 12345
        self.os_mock.getgid.return_value = 54321

        resourcepatcher = patch('pep3143daemon.daemon.resource', autospeck=True)
        self.resource_mock = resourcepatcher.start()

        signalpatcher = patch('pep3143daemon.daemon.signal', autospeck=True)
        self.signal_mock = signalpatcher.start()
        self.signal_mock.SIGTERM.return_value = 15

        socketpatcher = patch('pep3143daemon.daemon.socket', autospeck=True)
        self.socket_mock = socketpatcher.start()

        syspatcher = patch('pep3143daemon.daemon.sys', autospeck=False)
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
        pep3143daemon.daemon.close_filenos(set((1, 2, 4, 9)))
        self.os_mock.assert_has_calls(calls)

    def test_close_filenos_maxfd_unlimited(self):
        self.resource_mock.getrlimit.return_value = (12, self.resource_mock.RLIM_INFINITY)
        pep3143daemon.daemon.close_filenos(set((1, 2, 4, 9)))
        self.assertEqual(self.os_mock.close.call_count, 4092)

# Test default_signal_map()

    def test_default_signal_map(self):
        expected = {
            self.signal_mock.SIGTSTP: None,
            self.signal_mock.SIGTTIN: None,
            self.signal_mock.SIGTTOU: None,
            self.signal_mock.SIGTERM: 'terminate'}
        result = pep3143daemon.daemon.default_signal_map()
        self.assertEqual(result, expected)

    def test_default_signal_map_no_SIGTTOU(self):
        del self.signal_mock.SIGTTOU
        expected = {
            self.signal_mock.SIGTSTP: None,
            self.signal_mock.SIGTTIN: None,
            self.signal_mock.SIGTERM: 'terminate'}
        result = pep3143daemon.daemon.default_signal_map()
        self.assertEqual(result, expected)

# Test parent_is_init()

    def test_parent_is_init_true(self):
        self.os_mock.getppid.return_value = 1
        self.assertTrue(pep3143daemon.daemon.parent_is_init())

    def test_parent_is_init_false(self):
        self.os_mock.getppid.return_value = 12345
        self.assertFalse(pep3143daemon.daemon.parent_is_init())

# Test parent_is_inet()

    def test_parent_is_inet_true(self):
        self.sys_mock.__stdin__ = Mock()
        self.assertTrue(pep3143daemon.daemon.parent_is_inet())

    def test_parent_is_inet_true_sockerr(self):
        self.sys_mock.__stdin__ = Mock()
        sock = Mock()
        sock.getsockopt.side_effect = OSError('other socket error')
        self.socket_mock.fromfd.return_value = sock
        self.socket_mock.error = BaseException
        self.assertTrue(pep3143daemon.daemon.parent_is_inet())

    def test_parent_is_inet_false_ENOTSOCK(self):
        self.sys_mock.__stdin__ = Mock()
        sock = Mock()
        sock.getsockopt.side_effect = OSError(errno.ENOTSOCK)
        self.socket_mock.fromfd.return_value = sock
        self.socket_mock.error = BaseException
        self.assertFalse(pep3143daemon.daemon.parent_is_inet())

# test detach_required()

    def test_detach_required_false_parent_is_inet_true(self):
        parent_is_inetpatcher = patch('pep3143daemon.daemon.parent_is_init', autospeck=True)
        parent_is_inet_mock = parent_is_inetpatcher.start()
        parent_is_inet_mock.return_value = True

        parent_is_initpatcher = patch('pep3143daemon.daemon.parent_is_inet', autospeck=True)
        parent_is_init_mock = parent_is_initpatcher.start()
        parent_is_init_mock.return_value = False
        self.assertFalse(pep3143daemon.daemon.detach_required())

    def test_detach_required_false_parent_is_init_true(self):
        parent_is_inetpatcher = patch('pep3143daemon.daemon.parent_is_init', autospeck=True)
        parent_is_inet_mock = parent_is_inetpatcher.start()
        parent_is_inet_mock.return_value = False

        parent_is_initpatcher = patch('pep3143daemon.daemon.parent_is_inet', autospeck=True)
        parent_is_init_mock = parent_is_initpatcher.start()
        parent_is_init_mock.return_value = True
        self.assertFalse(pep3143daemon.daemon.detach_required())

    def test_detach_required_true(self):
        parent_is_inetpatcher = patch('pep3143daemon.daemon.parent_is_init', autospeck=True)
        parent_is_inet_mock = parent_is_inetpatcher.start()
        parent_is_inet_mock.return_value = False

        parent_is_initpatcher = patch('pep3143daemon.daemon.parent_is_inet', autospeck=True)
        parent_is_init_mock = parent_is_initpatcher.start()
        parent_is_init_mock.return_value = False
        self.assertTrue(pep3143daemon.daemon.detach_required())

# Test redirect_stream()
    def test_redirect_stream_None(self):
        file = Mock()
        file.fileno.return_value = 123
        pep3143daemon.daemon.redirect_stream(file, None)
        self.os_mock.assert_has_calls(
            [call.open(self.os_mock.devnull, self.os_mock.O_RDWR),
             call.dup2(self.os_mock.open(), 123)])

    def test_redirect_stream_fileno(self):
        file1 = Mock()
        file1.fileno.return_value = 123
        file2 = Mock()
        file2.fileno.return_value = 321
        pep3143daemon.daemon.redirect_stream(file1, file2)
        self.os_mock.assert_has_calls([call.dup2(321, 123)])
