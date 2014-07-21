__author__ = 'schlitzer'

import errno
import os
import resource
import signal
import six
import socket
import sys


class DaemonError(Exception):
    pass


class DaemonContext(object):
    """ Context for turning the current program into a daemon process.

        A `DaemonContext` instance represents the behaviour settings and
        process context for the program when it becomes a daemon. The
        behaviour and environment is customised by setting options on the
        instance, before calling the `open` method.

        Each option can be passed as a keyword argument to the `DaemonContext`
        constructor, or subsequently altered by assigning to an attribute on
        the instance at any time prior to calling `open`. That is, for
        options named `wibble` and `wubble`, the following invocation::

            foo = daemon.DaemonContext(wibble=bar, wubble=baz)
            foo.open()

        is equivalent to::

            foo = daemon.DaemonContext()
            foo.wibble = bar
            foo.wubble = baz
            foo.open()

        The following options are defined.

        `files_preserve`
            :Default: ``None``

            List of files that should *not* be closed when starting the
            daemon. If ``None``, all open file descriptors will be closed.

            Elements of the list are file descriptors (as returned by a file
            object's `fileno()` method) or Python `file` objects. Each
            specifies a file that is not to be closed during daemon start.

        `chroot_directory`
            :Default: ``None``

            Full path to a directory to set as the effective root directory of
            the process. If ``None``, specifies that the root directory is not
            to be changed.

        `working_directory`
            :Default: ``'/'``

            Full path of the working directory to which the process should
            change on daemon start.

            Since a filesystem cannot be unmounted if a process has its
            current working directory on that filesystem, this should either
            be left at default or set to a directory that is a sensible "home
            directory" for the daemon while it is running.

        `umask`
            :Default: ``0``

            File access creation mask ("umask") to set for the process on
            daemon start.

            Since a process inherits its umask from its parent process,
            starting the daemon will reset the umask to this value so that
            files are created by the daemon with access modes as it expects.

        `pidfile`
            :Default: ``None``

            Class for a PID lock file. When the daemon context opens
            the acquire method of the pidfile class is called

        `detach_process`
            :Default: ``None``

            If ``True``, detach the process context when opening the daemon
            context; if ``False``, do not detach.

            If unspecified (``None``) during initialisation of the instance,
            this will be set to ``True`` by default, and ``False`` only if
            detaching the process is determined to be redundant; for example,
            in the case when the process was started by `init`, by `initd`, or
            by `inetd`.

        `signal_map`
            :Default: system-dependent

            Mapping from operating system signals to callback actions.

            The mapping is used when the daemon context opens, and determines
            the action for each signal's signal handler:

            * A value of ``None`` will ignore the signal (by setting the
              signal action to ``signal.SIG_IGN``).

            * A string value will be used as the name of an attribute on the
              ``DaemonContext`` instance. The attribute's value will be used
              as the action for the signal handler.

            * Any other value will be used as the action for the
              signal handler. See the ``signal.signal`` documentation
              for details of the signal handler interface.

            The default value depends on which signals are defined on the
            running system. Each item from the list below whose signal is
            actually defined in the ``signal`` module will appear in the
            default map:

            * ``signal.SIGTTIN``: ``None``

            * ``signal.SIGTTOU``: ``None``

            * ``signal.SIGTSTP``: ``None``

            * ``signal.SIGTERM``: ``'terminate'``

            Depending on how the program will interact with its child
            processes, it may need to specify a signal map that
            includes the ``signal.SIGCHLD`` signal (received when a
            child process exits). See the specific operating system's
            documentation for more detail on how to determine what
            circumstances dictate the need for signal handlers.

        `uid`
            :Default: ``os.getuid()``

        `gid`
            :Default: ``os.getgid()``

            The user ID ("UID") value and group ID ("GID") value to switch
            the process to on daemon start.

            The default values, the real UID and GID of the process, will
            relinquish any effective privilege elevation inherited by the
            process.

        `prevent_core`
            :Default: ``True``

            If true, prevents the generation of core files, in order to avoid
            leaking sensitive information from daemons run as `root`.

        `stdin`
            :Default: ``None``

        `stdout`
            :Default: ``None``

        `stderr`
            :Default: ``None``

            Each of `stdin`, `stdout`, and `stderr` is a file-like object
            which will be used as the new file for the standard I/O stream
            `sys.stdin`, `sys.stdout`, and `sys.stderr` respectively. The file
            should therefore be open, with a minimum of mode 'r' in the case
            of `stdin`, and mode 'w+' in the case of `stdout` and `stderr`.

            If the object has a `fileno()` method that returns a file
            descriptor, the corresponding file will be excluded from being
            closed during daemon start (that is, it will be treated as though
            it were listed in `files_preserve`).

            If ``None``, the corresponding system stream is re-bound to the
            file named by `os.devnull`.

        """
    def __init__(
            self, chroot_directory=None, working_directory='/',
            umask=0, uid=None, gid=None, prevent_core=True,
            detach_process=None, files_preserve=None, pidfile=None,
            stdin=None, stdout=None, stderr=None, signal_map=None):
        """Setup a new instance"""
        self._is_open = False
        self.chroot_directory = chroot_directory
        self.umask = umask
        self.uid = uid if uid else os.getuid()
        self.gid = gid if gid else os.getgid()
        self.detach_process = detach_process if detach_process else detachrequired()
        self.signal_map = signal_map if signal_map else defaultsignalmap()
        self.files_preserve = files_preserve
        self.pidfile = pidfile
        self.prevent_core = prevent_core
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        if chroot_directory and not \
                working_directory.startswith(chroot_directory):
            self.working_directory = chroot_directory + working_directory
        else:
            self.working_directory = working_directory

    def __enter__(self):
        self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_signal_handler(self, target):
        """ Make the signal handler for a specified target object.

            If `target` is ``None``, returns ``signal.SIG_IGN``. If
            `target` is a string, returns the attribute of this
            instance named by that string. Otherwise, returns `target`
            itself.

            """
        if target is None:
            result = signal.SIG_IGN
        elif isinstance(target, six.string_types):
            result = getattr(self, target)
        else:
            result = target
        return result

    @property
    def is_open(self):
        """ ``True`` if the instance is currently open."""
        return self._is_open

    @property
    def _files_preserve(self):
        """ Return the set of file descriptors to exclude closing.

            Returns a set containing the file descriptors for the
            items in `files_preserve`, and also each of `stdin`,
            `stdout`, and `stderr`:

            * If the item is ``None``, it is omitted from the return
              set.

            * If the item has a ``fileno()`` method, that method's
              return value is in the return set.

            * If the item is from type ``int``, the item is in
              the return set.

            * Else, the Item is omitted.

            """
        result = set()
        if not self.files_preserve:
            files = []
        else:
            files = self.files_preserve
        files.extend([self.stdin, self.stdout, self.stderr])
        for item in files:
            if hasattr(item, 'fileno'):
                result.add(item.fileno())
            if isinstance(item, int):
                result.add(item)
        return result

    @property
    def _signal_handler_map(self):
        """ Make the map from signals to handlers for this instance.

            Constructs a map from signal numbers to handlers for this
            context instance, suitable for passing to
            `set_signal_handlers`.

            """
        signal_handler_map = {}
        for signum, handler in self.signal_map.items():
            signal_handler_map[signum] = self._get_signal_handler(handler)
        return signal_handler_map

    def close(self):
        """ Dummy function for not breaking code relying on it
        """
        pass


    def open(self):
        """ Become a daemon process.
            :Return: ``None``

            Open the daemon context, turning the current program into a daemon
            process. This performs the following steps:

            * If this instance's `is_open` property is true, return
              immediately. This makes it safe to call `open` multiple times on
              an instance.

            * If the `prevent_core` attribute is true, set the resource limits
              for the process to prevent any core dump from the process.

            * If the `chroot_directory` attribute is not ``None``, set the
              effective root directory of the process to that directory (via
              `os.chroot`).

              This allows running the daemon process inside a "chroot gaol"
              as a means of limiting the system's exposure to rogue behaviour
              by the process. Note that the specified directory needs to
              already be set up for this purpose.

            * Set the process UID and GID to the `uid` and `gid` attribute
              values.

            * Close all open file descriptors. This excludes those listed in
              the `files_preserve` attribute, and those that correspond to the
              `stdin`, `stdout`, or `stderr` attributes.

            * Change current working directory to the path specified by the
              `working_directory` attribute.

            * Reset the file access creation mask to the value specified by
              the `umask` attribute.

            * If the `detach_process` option is true, detach the current
              process into its own process group, and disassociate from any
              controlling terminal.

            * Set signal handlers as specified by the `signal_map` attribute.

            * If any of the attributes `stdin`, `stdout`, `stderr` are not
              ``None``, bind the system streams `sys.stdin`, `sys.stdout`,
              and/or `sys.stderr` to the files represented by the
              corresponding attributes. Where the attribute has a file
              descriptor, the descriptor is duplicated (instead of re-binding
              the name).

            * If the `pidfile` attribute is not ``None``, call its acquire
              method.

            * Mark this instance as open (for the purpose of future `open` and
              `close` calls).

            When the function returns, the running program is a daemon
            process.

            """
        if self.is_open:
            return
        try:
            os.chdir(self.working_directory)
            if self.chroot_directory:
                os.chroot(self.chroot_directory)
            os.setgid(self.gid)
            os.setuid(self.uid)
            os.umask(self.umask)
        except OSError as err:
            raise DaemonError('Setting up Environment failed: {0}'
                              .format(err))

        if self.prevent_core:
            try:
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            except Exception as err:
                raise DaemonError('Could not disable core files: {0}'
                                  .format(err))

        if self.detach_process:
            try:
                if os.fork() > 0:
                    sys.exit()
            except OSError as err:
                raise DaemonError('First fork failed: {0}'.format(err))
            os.setsid()
            try:
                if os.fork() > 0:
                    sys.exit()
            except OSError as err:
                raise DaemonError('Second fork failed: {0}'.format(err))

        for (signal_number, handler) in self._signal_handler_map.items():
            signal.signal(signal_number, handler)

        close_filenos(self._files_preserve)

        redirect_stream(sys.stdin, self.stdin)
        redirect_stream(sys.stdout, self.stdout)
        redirect_stream(sys.stderr, self.stderr)

        if self.pidfile:
            self.pidfile.acquire()

        self._is_open = True

    def terminate(self, signal_number, stack_frame):
        """ Signal handler for end-process signals.
            :Return: ``None``

            Signal handler for the ``signal.SIGTERM`` signal. Performs the
            following step:

            * Raise a ``SystemExit`` exception explaining the signal.

            """
        raise SystemExit('Terminating on signal {0}'.format(signal_number))


def close_filenos(preserve):
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if maxfd == resource.RLIM_INFINITY:
        maxfd = 4096
    for fileno in range(maxfd):
        if not fileno in preserve:
            try:
                os.close(fileno)
            except OSError as err:
                if not err.errno == errno.EBADF:
                    raise DaemonError('Failed to close file descriptor {0}: {1}'
                                      .format(fileno, err))


def defaultsignalmap():
    name_map = {
        'SIGTSTP': None,
        'SIGTTIN': None,
        'SIGTTOU': None,
        'SIGTERM': 'terminate'}
    signal_map = {}
    for name, target in name_map.items():
        if hasattr(signal, name):
            signal_map[getattr(signal, name)] = target

    return signal_map


def parentisinit():
    if os.getppid() == 1:
        return True
    return False


def parentisinet():
    result = False
    sock = socket.fromfd(
        sys.__stdin__.fileno(),
        socket.AF_INET,
        socket.SOCK_RAW)
    try:
        sock.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE)
        result = True
    except OSError as err:
        if err.args[0] == errno.ENOTSOCK:
            pass
        else:
            result = True
    except socket.error as err:
        if err.args[0] == errno.ENOTSOCK:
            pass
        else:
            result = True
    return result


def detachrequired():
    if parentisinet() or parentisinit():
        return False
    else:
        return True


def redirect_stream(system, target):
    if target is None:
        target_fd = os.open(os.devnull, os.O_RDWR)
    else:
        target_fd = target.fileno()
    try:
        os.dup2(target_fd, system.fileno())
    except OSError as err:
        raise DaemonError('Could not redirect {0} to {1}: {2}'
                          .format(system, target, err))
