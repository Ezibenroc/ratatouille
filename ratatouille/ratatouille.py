import csv
import datetime
import time
import psutil
import re
import socket
import signal
import sys


class AbstractWatcher:
    def __init__(self):
        self.nb_cores = psutil.cpu_count(logical=False)
        self.nb_threads = psutil.cpu_count(logical=True)
        assert self.nb_threads % self.nb_cores == 0

    def get_values(self):
        raise NotImplementedError()

    def build_header(self, prefix, suffixes):
        return ['%s%s' % (prefix, suf) for suf in suffixes]


class CPULoad(AbstractWatcher):
    def __init__(self):
        super().__init__()
        self.header = self.build_header('load_core_', range(len(self.get_values())))

    def get_values(self):
        values = psutil.cpu_percent(percpu=True)
        assert len(values) in (self.nb_cores, self.nb_threads)
        return values[:self.nb_cores]


class CPUStats(AbstractWatcher):
    header = ['ctx_switches', 'interrupts', 'soft_interrupts']

    @staticmethod
    def get_values():
        val = psutil.cpu_stats()
        return [val.ctx_switches, val.interrupts, val.soft_interrupts]


class CPUFreq(AbstractWatcher):
    def __init__(self):
        super().__init__()
        self.header = self.build_header('frequency_core_', range(len(self.get_values())))

    def get_values(self):
        values = psutil.cpu_freq(percpu=True)
        assert len(values) in (self.nb_cores, self.nb_threads)
        return [int(freq.current*1e6) for freq in values[:self.nb_cores]]


class MemoryUsage(AbstractWatcher):
    header = ['memory_available_percent', 'memory_available']

    @staticmethod
    def get_values():
        mem = psutil.virtual_memory()
        return [100-mem.percent, mem.available]


class Temperature(AbstractWatcher):
    reg = re.compile('Core (?P<id>[0-9]+)')

    def __init__(self):
        super().__init__()
        self.header = self.build_header('temperature_core_', range(len(self.get_values())))

    def get_values(self):
        coretemps = psutil.sensors_temperatures()['coretemp']
        values = []
        for temp in coretemps:
            match = self.reg.match(temp.label)
            if match:
                values.append((int(match.group('id')), temp.current))
        values.sort(key = lambda t: t[0])
        assert len(values) == self.nb_cores
        return [t[1] for t in values]


class Network(AbstractWatcher):
    def __init__(self):
        super().__init__()
        self.interfaces = list(psutil.net_io_counters(pernic=True).keys())
        self.header = []
        for nic in self.interfaces:
            self.header.extend(['bytes_sent_%s' % nic, 'bytes_recv_%s' % nic])

    def get_values(self):
        data = psutil.net_io_counters(pernic=True)
        values = []
        for nic in self.interfaces:
            values.extend([data[nic].bytes_sent, data[nic].bytes_recv])
        return values


class Monitor:
    def __init__(self, watchers, output_file, time_interval):
        self.watchers = watchers
        self.time_interval = time_interval
        self.file = output_file
        self.writer = csv.writer(self.file)
        header = ['hostname', 'timestamp']
        for watcher in self.watchers:
            header.extend(watcher.header)
        self.writer.writerow(header)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler)

    def signal_handler(self, sig, frame):
        self.file.flush()
        sys.exit(0)

    def watch(self):
        timestamp = str(datetime.datetime.now())
        row = [socket.gethostname(), timestamp]
        for watcher in self.watchers:
            row.extend(watcher.get_values())
        self.writer.writerow(row)

    def start_loop(self):
        while True:
            self.watch()
            time.sleep(self.time_interval)


monitor_classes = [
    CPUStats,
    MemoryUsage,
    Temperature,
    CPUFreq,
    CPULoad,
    Network,
]


class Drawer:
    def __init__(self, input_file):
        import pandas
        self.input_file = input_file
        self.data = pandas.read_csv(input_file)
        self.data.timestamp = pandas.to_datetime(self.data.timestamp)

    def plot(self):
        from plotnine import ggplot, theme_bw, aes, geom_line, expand_limits, scale_x_datetime, ylab, facet_wrap, theme
        from mizani.formatters import date_format
        data = self.data.copy()
        data['time_diff'] = data['timestamp'][1:].reset_index(drop=True) - data['timestamp'][:-1].reset_index(drop=True)
        time_step = data['time_diff'].median()
        breakpoints = list(data[data['time_diff'] > time_step * 10].timestamp)
        breakpoints = [data['timestamp'].min(), *breakpoints, data['timestamp'].max()]
        data = data.drop('time_diff', 1).melt('timestamp')
        plot = ggplot() + theme_bw()
        for min_t, max_t in zip(breakpoints[:-1], breakpoints[1:]):
            tmp = data[(data['timestamp'] > min_t) & (data['timestamp'] < max_t)]
            plot += geom_line(tmp, aes(x='timestamp', y='value', color='variable'), show_legend=False)
        plot += facet_wrap(['variable'], scales='free')
        timedelta = self.data.timestamp.max() - self.data.timestamp.min()
        if timedelta.days > 2:
            plot += scale_x_datetime(labels=date_format('%Y/%m/%d'))
        else:
            plot += scale_x_datetime(labels=date_format('%H:%M'))
        plot += ylab('Value')
        return plot
