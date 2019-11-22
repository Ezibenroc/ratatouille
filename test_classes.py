from ratatouille.ratatouille import *
import os
from psutil import cpu_count, net_io_counters


def test_monitors():
    classes = [
        (CPULoad, cpu_count(logical=False)),
        (MemoryUsage, 2),
        (Temperature, cpu_count(logical=False)),
        (CPUFreq, cpu_count(logical=False)),
        (CPUStats, 3),
        (Network, 2*len(net_io_counters(pernic=True)))
    ]
    for cls, nb_values in classes:
        mon = cls()
        values = mon.get_values()
        assert len(mon.header) == len(values)
        assert len(values) == nb_values
