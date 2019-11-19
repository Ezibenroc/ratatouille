import csv
import datetime
import time
import psutil
import re


class CPULoad:
    header = ['cpu_load']

    @staticmethod
    def get_values():
        return [psutil.cpu_percent()]


class CPUFreq:
    def __init__(self):
        freqs = self.get_values()
        self.header = ['frequency_core_%d' % i for i in range(len(freqs))]

    @classmethod
    def get_values(cls):
        frequencies = psutil.cpu_freq(percpu=True)
        return [int(freq.current*1e6) for freq in frequencies]


class MemoryUsage:
    header = ['memory_usage']

    @staticmethod
    def get_values():
        return [psutil.virtual_memory().percent]


class Temperature:
    reg = re.compile('Core (?P<id>[0-9]+)')

    def __init__(self):
        temps = self.get_values()
        self.header = ['temperature_core_%d' % i for i in range(len(temps))]

    @classmethod
    def get_values(cls):
        coretemps = psutil.sensors_temperatures()['coretemp']
        values = []
        for temp in coretemps:
            match = cls.reg.match(temp.label)
            if match:
                values.append((int(match.group('id')), temp.current))
        values.sort(key = lambda t: t[0])
        return [t[1] for t in values]


class Monitor:
    def __init__(self, watchers, output_file, time_interval):
        self.watchers = watchers
        self.time_interval = time_interval
        self.file = output_file
        self.writer = csv.writer(self.file)
        header = ['timestamp']
        for watcher in self.watchers:
            header.extend(watcher.header)
        self.writer.writerow(header)

    def watch(self):
        timestamp = str(datetime.datetime.now())
        row = [timestamp]
        for watcher in self.watchers:
            row.extend(watcher.get_values())
        self.writer.writerow(row)
        self.file.flush()

    def start_loop(self):
        try:
            while True:
                self.watch()
                time.sleep(self.time_interval)
        except KeyboardInterrupt:
            return


monitor_classes = [
    CPULoad,
    MemoryUsage,
    Temperature,
    CPUFreq,
]


class Drawer:
    def __init__(self, input_file):
        import pandas
        self.input_file = input_file
        self.data = pandas.read_csv(input_file)
        self.data.timestamp = pandas.to_datetime(self.data.timestamp)

    def plot(self):
        from plotnine import ggplot, theme_bw, aes, geom_line, expand_limits, scale_x_datetime, ylab
        from mizani.formatters import date_format
        data = self.data.copy()
        data['time_diff'] = data['timestamp'][1:].reset_index(drop=True) - data['timestamp'][:-1].reset_index(drop=True)
        time_step = data['time_diff'].median()
        breakpoints = list(data[data['time_diff'] > time_step * 10].timestamp)
        breakpoints = [data['timestamp'].min(), *breakpoints, data['timestamp'].max()]
        data = data.drop('time_diff', 1).melt('timestamp')
        plot = ggplot() + theme_bw()
        plot += expand_limits(y=0)
        plot += expand_limits(y=100)
        for min_t, max_t in zip(breakpoints[:-1], breakpoints[1:]):
            tmp = data[(data['timestamp'] > min_t) & (data['timestamp'] < max_t)]
            plot += geom_line(tmp, aes(x='timestamp', y='value', color='variable'))
        timedelta = self.data.timestamp.max() - self.data.timestamp.min()
        if timedelta.days > 2:
            plot += scale_x_datetime(labels=date_format('%Y/%m/%d'))
        else:
            plot += scale_x_datetime(labels=date_format('%H:%M'))
        plot += ylab('Usage (%)')
        return plot
