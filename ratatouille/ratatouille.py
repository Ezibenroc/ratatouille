import csv
import datetime
import time
import psutil
import re
import socket
import signal
import sys
import os
from collections import OrderedDict


class RatatouilleDependencyError(Exception):
    pass


class RatatouillePortabilityError(Exception):
    pass


class AbstractWatcher:
    def __init__(self):
        self.first_values = self.get_values()
        self.nb_values = len(self.first_values)

    def get_values(self):
        raise NotImplementedError()

    def checked_get_values(self):
        values = self.get_values()
        assert self.nb_values == len(values)
        return values

    def build_header(self, prefix, suffixes):
        return ['%s%s' % (prefix, suf) for suf in suffixes]


class FileWatcher(AbstractWatcher):
    def __init__(self, prefix, name, suffix):
        '''
        Suppose files of the form prefix/name42/suffix
        '''
        self.files = {}
        regex = re.compile('^%s(?P<id>\\d+)$' % name)
        for dirname in os.listdir(prefix):
            match = regex.match(dirname)
            if match:
                new_id = int(match.group('id'))
                filename = os.path.join(prefix, dirname, suffix)
                if not os.path.isfile(filename):
                    raise RatatouillePortabilityError(f'File {filename} not found')
                self.files[new_id] = filename
        super().__init__()

    def get_values(self):
        values = []
        for i, filename in self.files.items():
            values.append((i, int(get_string_in_file(filename))))
        values.sort()
        return [val[1] for val in values]


class CPULoad(AbstractWatcher):
    header = ['cpu_load']

    def get_values(self):
        return [psutil.cpu_percent()]


class CPUStats(AbstractWatcher):
    header = ['ctx_switches', 'interrupts', 'soft_interrupts']

    @staticmethod
    def get_values():
        val = psutil.cpu_stats()
        return [val.ctx_switches, val.interrupts, val.soft_interrupts]


class CPUFreq(FileWatcher):
    def __init__(self):
        try:
            super().__init__('/sys/devices/system/cpu', 'cpu', 'cpufreq/scaling_cur_freq')
        except RatatouillePortabilityError:
            raise RatatouillePortabilityError('CPU frequency unavailable, could not read cpufreq files')
        self.header = self.build_header('frequency_core_', range(self.nb_values))

    def get_values(self):
        frequencies = super().get_values()
        return [freq*1000 for freq in frequencies]


class CPUPower(AbstractWatcher):
    def __init__(self):
        try:
            self.files = self.get_init_files('/sys/devices/virtual/powercap/intel-rapl/', 'intel-rapl', 'energy_uj')
        except FileNotFoundError:
            raise RatatouillePortabilityError('Power monitoring unavailable, could not read intel-rapl files')

        self.header = ["power_%s" % label for label in self.files.keys()]
        super().__init__()


    def get_init_files(self, prefix, name, suffix, label_suffix = ''):
        files = OrderedDict()
        regex = re.compile('^%s:(?P<id>\\d+)$' % name)
        for dirname in os.listdir(prefix):
            match = regex.match(dirname)
            if match: # dirname is of the form intel-rapl:<package-id>
                # Add the package file
                label = get_string_in_file(os.path.join(prefix, dirname, "name")) + label_suffix
                files[label] = os.path.join(prefix, dirname, suffix)

                # Get core, uncore and dram files
                regex2 = re.compile('^%s:(?P<id>\\d+)$' % (dirname))
                for dirname2 in os.listdir("%s%s" % (prefix, dirname)):
                    match2 = regex2.match(dirname2)
                    if match2: # dirname2 is of the form intel-rapl:<package-id>:<id>
                        label2 = "%s_%s%s" % (label, get_string_in_file(os.path.join(prefix, dirname, dirname2, "name")), label_suffix)
                        files[label2] = os.path.join(prefix, dirname, dirname2, suffix)
        return files


    def get_values(self):
        energies = []
        for filename in self.files.values():
            energies.append(int(get_string_in_file(filename)))

        instant = time.time()
        try:
            duration = instant - self.last_instant
            powers = [(new-old)*1e-6/duration for new, old in zip(energies, self.last_energies)]
            for i, p in enumerate(powers):
                if p < 0:
                    powers[i] = float('nan')
        except AttributeError:
            powers = [float('nan') for _ in energies]
        self.last_instant = instant
        self.last_energies = energies
        return powers


def get_string_in_file(filename):
    with open(filename) as f:
        lines = f.readlines()
        assert len(lines) == 1
        return lines[0].rstrip('\n')


class MemoryUsage(AbstractWatcher):
    header = ['memory_available_percent', 'memory_available']

    @staticmethod
    def get_values():
        mem = psutil.virtual_memory()
        return [100-mem.percent, mem.available]


class Temperature(AbstractWatcher):
    reg = re.compile('(?:Core (?P<core_id>[0-9]+))|(?:(?:Package|Physical) id (?P<package_id>[0-9]+))')

    def __init__(self):
        self.header = list(self._get_values_dict().keys())
        super().__init__()

    @classmethod
    def _get_core_temps(cls, temperatures):
        coretemps = temperatures.get('coretemp', [])
        packages = set()
        packages_values = []
        # First, we iterate on the labels to get all the packages ID
        for temp in coretemps:
            match = cls.reg.match(temp.label)
            assert match is not None
            package_id = match.groupdict()['package_id']
            if package_id is not None:
                package_id = int(package_id)
                assert package_id not in packages
                packages.add(package_id)
                packages_values.append((package_id, temp.current))
        # If there are 4 distinct packages, we expect them to be labelled as 0,1,2,3
        nb_packages = len(packages)
        assert packages == set(range(nb_packages))
        # Finally, we iterate a second time to build the list of core temperatures
        package_id = -1
        values = []
        for temp in coretemps:
            match = cls.reg.match(temp.label)
            if match.groupdict()['package_id'] is not None:
                package_id = int(match.groupdict()['package_id'])
            else:
                core_id = match.groupdict()['core_id']
                assert core_id is not None
                core_id = int(core_id)
                core_id = core_id*nb_packages + package_id
                values.append((core_id, temp.current))
        values.sort(key = lambda t: t[0])
        result = {'temperature_core_%d' % t[0]: t[1] for t in values}
        result.update({'temperature_cpu_%d' % t[0]: t[1] for t in packages_values})
        return result

    @classmethod
    def _get_values_dict(cls):
        temperatures = psutil.sensors_temperatures()
        alltemps = cls._get_core_temps(temperatures)
        for key, value in sorted(temperatures.items()):
            if key == 'coretemp':
                continue
            for elt in value:
                label = 'temperature_%s' % key
                if elt.label != '':
                    label = '%s_%s' % (label, elt.label)

                alltemps[label] = elt.current

        return alltemps

    def get_values(self):
        values = self._get_values_dict()
        return [values[k] for k in self.header]


class FanSpeed(AbstractWatcher):
    def __init__(self):
        self.header = list(self._get_values_dict().keys())
        super().__init__()

    @classmethod
    def _get_values_dict(cls):
        speeds = psutil.sensors_fans()
        values = {}
        for key, value in sorted(speeds.items()):
            for elt in value:

                label = "speed_%s" % key
                if elt.label != '':
                    label = "%s_%s" % (label, (elt.label.replace(' ', '_')))

                values[label] = elt.current

        return values


    def get_values(self):
        values = self._get_values_dict()
        return [values[k] for k in self.header]


class Network(AbstractWatcher):
    def __init__(self):
        self.interfaces = list(sorted(psutil.net_io_counters(pernic=True).keys()))
        super().__init__()
        self.header = []
        for nic in self.interfaces:
            self.header.extend(['bytes_sent_%s' % nic, 'bytes_recv_%s' % nic])

    def get_values(self):
        data = psutil.net_io_counters(pernic=True)
        byte_numbers = []
        instant = time.time()
        for nic in self.interfaces:
            byte_numbers.extend([data[nic].bytes_sent, data[nic].bytes_recv])
        try:
            duration = instant - self.last_instant
            speeds = [(new-old)/duration for new, old in zip(byte_numbers, self.last_byte_numbers)]
            for i, p in enumerate(speeds):
                if p < 0:
                    speeds[i] = float('nan')
        except AttributeError:
            speeds = [float('nan') for _ in byte_numbers]
        self.last_instant = instant
        self.last_byte_numbers = byte_numbers
        return speeds


class Monitor:
    def __init__(self, watchers, output_file, time_interval):
        self.watchers = watchers
        self.time_interval = time_interval
        self.next_watch = time.time() + self.time_interval
        self.file = output_file
        self.writer = csv.writer(self.file)
        self.hostname = socket.gethostname()
        header = ['hostname', 'timestamp']
        for watcher in self.watchers:
            header.extend(watcher.header)
        self.writer.writerow(header)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler)
        self.continue_monitoring = True

    def signal_handler(self, sig, frame):
        self.file.flush()
        self.continue_monitoring = False

    def watch(self):
        timestamp = str(datetime.datetime.now())
        row = [self.hostname, timestamp]
        for watcher in self.watchers:
            row.extend(watcher.get_values())
        self.writer.writerow(row)

    def start_loop(self):
        while self.continue_monitoring:
            sleep_time = self.next_watch - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.next_watch = time.time() + self.time_interval
            self.watch()

monitor_classes = {
    'cpu_stats': CPUStats,
    'memory_usage': MemoryUsage,
    'temperature': Temperature,
    'cpu_freq': CPUFreq,
    'cpu_power': CPUPower,
    'cpu_load': CPULoad,
    'network': Network,
    'fan_speed': FanSpeed,
}


class Drawer:
    def __init__(self, input_file):
        try:
            import pandas
        except ImportError:
            msg = """Package 'pandas' is required for the plot functionnality.
            Try installing it with 'pip install pandas'.
            """
            raise RatatouilleDependencyError(msg)
        self.input_file = input_file
        self.data = pandas.read_csv(input_file)
        self.data.timestamp = pandas.to_datetime(self.data.timestamp)

    def create_plot(self, columns):
        for col in columns:
            if col not in self.data.columns:
                raise ValueError('No column "%s" in the data' % col)
        try:
            from plotnine import ggplot, theme_bw, aes, geom_line, expand_limits, scale_x_datetime, ylab, facet_wrap, theme
            from mizani.formatters import date_format
        except ImportError:
            msg = """Package 'plotnine' is required for the plot functionnality.
            Try installing it with 'pip install plotnine'.
            """
            raise RatatouilleDependencyError(msg)
        data = self.data.copy()
        if len(columns) > 0:
            data = data[['timestamp'] + columns]
        else:
            if 'hostname' in data:
                data.drop('hostname', axis=1, inplace=True)
        data['time_diff'] = data['timestamp'][1:].reset_index(drop=True) - data['timestamp'][:-1].reset_index(drop=True)
        time_step = data['time_diff'].median()
        breakpoints = list(data[data['time_diff'] > time_step * 10].timestamp)
        breakpoints = [data['timestamp'].min(), *breakpoints, data['timestamp'].max()]
        data = data.drop('time_diff', 1).melt('timestamp')
        import pandas
        if len(columns) > 0:
            data['variable'] = pandas.Categorical(data['variable'], categories=columns)
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


def merge_files(input_files, output_file):
    try:
        import pandas
    except ImportError:
        msg = """Package 'pandas' is required for the merge functionnality.
        Try installing it with 'pip install pandas'.
        """
        raise RatatouilleDependencyError(msg)
    dataframes = [pandas.read_csv(f) for f in input_files]
    pandas.concat(dataframes, sort=False).to_csv(output_file, index=False)
