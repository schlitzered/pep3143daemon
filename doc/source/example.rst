Usage Example
*************

Example Daemon
==============

Simple Daemon that sends a syslog message every 2 seconds,
and terminates after two minutes::

    from pep3143daemon import DaemonContext, PidFile
    import syslog, time


    counter = 60
    pid='/tmp/pep3134daemon_example.pid'

    pidfile = PidFile(pid)
    daemon = DaemonContext(pidfile=pidfile)
    # we could have written this also as:
    # daemon.pidfile = pidfile

    print('pidfile is: {0}'.format(pid))
    print('daemonizing...')

    daemon.open()

    syslog.syslog('pep3134daemon_example: daemonized')

    while counter > 0:
        syslog.syslog('pep3134daemon_example: still running')
        counter -= 1
        syslog.syslog('pep3134daemon_example: counter: {0}'.format(counter))
        time.sleep(2)

    syslog.syslog('pep3134daemon_example: terminating...')