# Ratatouille

## Installation

```sh
pip install git+https://github.com/Ezibenroc/ratatouille.git
```

## Example of usage

Collect data in file `/tmp/data.csv` with a 3 seconds interval (press Ctr-C to stop).
```sh
ratatouille collect -t 3 /tmp/data.csv
```

Plot the data stored in file `/tmp/data.csv`.
```sh
ratatouille plot /tmp/data.csv
```

For this last command, you need to install extra dependencies:
```sh
pip install pandas plotnine
```
