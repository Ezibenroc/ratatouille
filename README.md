# Ratatouille

## Installation

The best way to install `ratatouille` is to use one of the
[releases](https://github.com/Ezibenroc/ratatouille/releases). For instance, to install the version 0.0.2:
```sh
pip install https://github.com/Ezibenroc/ratatouille/releases/download/0.0.2/ratatouille-0.0.2-py3-none-any.whl
```

Alternatively, you can install from `master` as follows:
```sh
pip install git+https://github.com/Ezibenroc/ratatouille.git
```

## Example of usage

Collect data in file `/tmp/data.csv` with a 3 seconds interval (press Ctr-C to stop).
```sh
ratatouille collect -t 3 all /tmp/data.csv
```

Collect only the temperature and frequency:
```sh
ratatouille collect -t 3 cpu_freq temperature /tmp/data.csv
```

Plot the data stored in file `/tmp/data.csv`.
```sh
ratatouille plot /tmp/data.csv
```

For this last command, you need to install extra dependencies:
```sh
pip install pandas plotnine
```

## Collected data

When collecting data you can either collect all data (with the `all` target argument) or a subset of the data:

- `cpu_freq` collects the frequency (in `Hertz`) of each *logical* CPU core listed in `/sys/devices/system/cpu/`.
- `cpu_load` collects the percentage load of the CPUs.
- `cpu_power` computes the average power consumption (in `Watts`) of each package listed in `/sys/devices/virtual/powercap/intel-rapl/` between two intervals. Additional values for the `core`, `uncore` and `dram` are also collected if available.
- `cpu_stats` collects the total number of context switches, interrupts and soft_interrupts since boot.
- `memory_usage` collects the current memory available (in bytes) and its percentage over the total memory.
- `network` collects the total number of bytes sent and received on each network interface.
- `temperature` collects the temperature (in Celsius or Farenheit degrees, depending on your configuration) of each *physical* CPU core and other thermal sensors.

Notice that `cpu_load`, `cpu_stats`, `memory_usage`, `network` and `temperature` rely on [psutil](https://github.com/giampaolo/psutil) to collect data.