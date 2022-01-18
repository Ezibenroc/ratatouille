#!/usr/bin/env python3

import sys
from setuptools import setup
import subprocess

VERSION = '0.1.0'


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

try:
    with open('README.md') as f:
        long_description = ''.join(f.readlines())
except (IOError, ImportError, RuntimeError):
    print('Could not generate long description.')
    long_description = ''

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
          long_description_content_type="text/markdown",
          long_description=long_description,
          author='Tom Cornebize',
          author_email='tom.cornebize@gmail.com',
          packages=['ratatouille'],
          entry_points={
              'console_scripts': ['ratatouille = ratatouille.__main__:main',
                                  ]
          },
          install_requires=[
              'psutil>=5.8.0',
          ],
          url='https://github.com/Ezibenroc/ratatouille',
          license='MIT',
          classifiers=[
              'License :: OSI Approved :: MIT License',
              'Intended Audience :: Science/Research',
              'Intended Audience :: System Administrators',
              'Operating System :: POSIX :: Linux',
              'Programming Language :: Python :: 3.7',
              'Programming Language :: Python :: 3.8',
              'Programming Language :: Python :: 3.9',
          ],
          )
