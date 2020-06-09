#!/usr/bin/env python3

import sys
from setuptools import setup
import subprocess

VERSION = '0.0.2'


class CommandError(Exception):
    pass


def run(args):
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise CommandError('Error with the command %s.\n' % ' '.join(args))
    return stdout.decode('ascii').strip()


def git_version():
    return run(['git', 'rev-parse', 'HEAD'])


def git_tag():
    return run(['git', 'describe', '--always', '--dirty'])


def write_version(filename, version_dict):
    with open(filename, 'w') as f:
        for version_name in version_dict:
            f.write('%s = "%s"\n' % (version_name, version_dict[version_name]))


if __name__ == '__main__':
    try:
        write_version('ratatouille/version.py', {
                '__version__': VERSION,
                '__git_version__': git_version(),
            })
    except CommandError as e:
        if sys.argv[0] != '-c':
            sys.exit(e)
    setup(name='ratatouille',
          version=VERSION,
          description='System usage monitoring tool',
          author='Tom Cornebize',
          author_email='tom.cornebize@gmail.com',
          packages=['ratatouille'],
          entry_points={
              'console_scripts': ['ratatouille = ratatouille.__main__:main',
                                  ]
          },
          install_requires=[
              'psutil<5.7.0',
              'pandas',
          ],
          url='https://github.com/Ezibenroc/ratatouille',
          license='MIT',
          classifiers=[
              'License :: OSI Approved :: MIT License',
              'Intended Audience :: Developers',
              'Operating System :: POSIX :: Linux',
              'Operating System :: MacOS :: MacOS X',
              'Programming Language :: Python :: 3.6',
          ],
          )
