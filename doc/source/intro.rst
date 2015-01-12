Introduction
************

The main reason for the development of pep3143daemon was that the
original implementation of PEP 3143
`python-daemon <https://pypi.python.org/pypi/python-daemon>`_
seemed to be unmaintained, and failed to run under python 3.

Also the bundled Pidfile implementation was not working anymore, because
of incompatibilities with newer version of external libraries.

The goal of pep3143daemon is to create a complete, and working PEP 3143
library. For this reason, also a working PidFile class is bundled with this Package.

The package only depend on Python build in modules.

This package is tested withPython 3.3/3.4 and Python 2.7, using the
unittest framework, and additionally for python 2.7 with the mock library,
which is part of unittest in Python 3.


Differences
-----------

pep3143daemon mostly sticks to the PEP, but does not implement
some details that seem to be wrong.
The main difference is the DaemonContext.close() method.

The close method of DeamonContext is implemented as a dummy method.
According to the PEP, this method should mark the instance as closed.
It would also call the __exit__ method of a PidFile context manager,
if one is attached.

The close method is not implemented, because it is not possible to close a
daemon in a sane way. But worse, removing the PidFile before the daemon is
terminated, would allow a second instance to start. Which can lead to
undefined behaviour.

The removal of the PidFile is now implemented in the PidFile class,
distributed with the pep3143daemon package.
The file will be removed via an atexit call.

The rest of the implementation sticks to the PEP 3143.