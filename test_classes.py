from ratatouille.ratatouille import *
import os
from psutil import cpu_count, net_io_counters


def test_monitors():
    classes = [
        (CPULoad, 1),
        (MemoryUsage, 2),
        (CPUFreq, cpu_count(logical=True)),
        (CPUStats, 3),
        (Network, 2*len(net_io_counters(pernic=True)))
    ]
    for cls, nb_values in classes:
        mon = cls()
        values = mon.get_values()
        assert len(mon.header) == len(values)
        assert len(values) == nb_values
    temp = Temperature()
    assert len(temp.header) == len(temp.get_values())
    assert len(temp.get_values()) >= cpu_count(logical=False)
