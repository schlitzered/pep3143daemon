__author__ = 'schlitzer'
""" Library to implement a well-behaved Unix daemon process.

    This library implements the well-behaved daemon specification of
    :pep:`3143`, "Standard daemon process library".

    A well-behaved Unix daemon process is tricky to get right, but the
    required steps are much the same for every daemon program. A
    `DaemonContext` instance holds the behaviour and configured
    process environment for the program; use the instance as a context
    manager to enter a daemon state.

    Simple example of usage::

        import daemon

        from spam import do_main_program

        with daemon.DaemonContext():
            do_main_program()

    Customisation of the steps to become a daemon is available by
    setting options on the `DaemonContext` instance; see the
    documentation for that class for each option.

    """

from pep3143daemon.Daemon import DaemonContext
