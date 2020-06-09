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
