import sys
import csv
import datetime
import argparse
import time
import psutil


class CPULoad:
    header = 'cpu_load'

    @staticmethod
    def get_value():
        return psutil.cpu_percent()


class MemoryUsage:
    header = 'memory_usage'

    @staticmethod
    def get_value():
        return psutil.virtual_memory().percent


class Monitor:
    def __init__(self, watchers, output_file, time_interval):
        self.watchers = watchers
        self.time_interval = time_interval
        self.file = output_file
        self.writer = csv.writer(self.file)
        self.writer.writerow(['timestamp'] + [watcher.header for watcher in self.watchers])

    def watch(self):
        timestamp = str(datetime.datetime.now())
        self.writer.writerow([timestamp] + [watcher.get_value() for watcher in self.watchers])

    def start_loop(self):
        try:
            while True:
                self.watch()
                time.sleep(self.time_interval)
        except KeyboardInterrupt:
            return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Monitoring of the system resources')
    parser.add_argument('--time_interval', '-t', type=int, default=60,
                        help='Period of the measures, in seconds.')
    parser.add_argument('output_file', type=argparse.FileType('w'),
                        help='Output file for the measures.')
    args = parser.parse_args(sys.argv[1:])

    monitor = Monitor([CPULoad, MemoryUsage], time_interval=args.time_interval,
                      output_file=args.output_file)
    t = time.time()
    monitor.start_loop()
    t = time.time() - t
    print('Monitored the sytem for %d seconds' % int(t))
