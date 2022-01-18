import time
import signal
from subprocess import run, Popen
import os
import math


def test_version():
    rat_version = run(['ratatouille', '--git-version'], capture_output=True)
    rat_version = rat_version.stdout.decode().strip()
    git_version = run(['git', 'rev-parse', 'HEAD'], capture_output=True)
    git_version = git_version.stdout.decode().strip()
    assert rat_version == 'ratatouille %s' % git_version


def test_collect(period=2, run_time=5, filename='/tmp/test.csv'):
    proc = Popen(['ratatouille', 'collect', '-t', str(period), 'all', filename])
    time.sleep(run_time)
    proc.send_signal(signal.SIGINT)
    assert proc.wait() == 0
    assert os.path.isfile(filename)
    with open(filename) as f:
        lines = f.readlines()
    assert len(lines) >= math.ceil(run_time/period)
