from ratatouille.ratatouille import *
import os
from psutil import cpu_count


def test_monitors():
    classes = [
        (CPULoad, cpu_count(logical=True)),
        (MemoryUsage, 2),
        (Temperature, cpu_count(logical=False)),
        (CPUFreq, cpu_count(logical=True)),
        (CPUStats, 3),
    ]
    for cls, nb_values in classes:
        mon = cls()
        values = mon.get_values()
        assert len(mon.header) == len(values)
        assert len(values) == nb_values
