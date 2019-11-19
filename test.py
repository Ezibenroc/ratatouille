from ratatouille.ratatouille import *
import os


def test_monitors():
    classes = [
        (CPULoad, 1),
        (MemoryUsage, 1),
        (Temperature, os.cpu_count()//2),
    ]
    for cls, nb_values in classes:
        mon = cls()
        values = mon.get_values()
        assert len(mon.header) == len(values)
        assert len(values) == nb_values
