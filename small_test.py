#! /usr/bin/env python3

from subprocess import run


def test_version():
    rat_version = run(['ratatouille', '--git-version'], capture_output=True)
    rat_version = rat_version.stdout.decode().strip()
    git_version = run(['git', 'rev-parse', 'HEAD'], capture_output=True)
    git_version = git_version.stdout.decode().strip()
    assert rat_version == 'ratatouille %s' % git_version
