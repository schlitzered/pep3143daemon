from setuptools import setup

import pep3143daemon

setup(
    name='pep3143daemon',
    version='0.0.6',
    description='Implementation of PEP 3143, a unix daemon',
    long_description=pep3143daemon.__doc__,
    packages=['pep3143daemon'],
    url='https://github.com/schlitzered/pep3143daemon',
    license='MIT',
    author='schlitzer',
    author_email='stephan.schultchen@gmail.com',
    test_suite='test',
    platforms='posix',
    classifiers=[
            'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: MIT License',
            'Operating System :: POSIX',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4'
    ],
    keywords=[
        'daemon',
        'daemonize'
        'daemonizing'
        'fork',
        'pep 3143',
        '3143'
    ]
)
