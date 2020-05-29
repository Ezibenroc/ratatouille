import argparse
import time
import sys
import pandas
from .ratatouille import Monitor, Drawer, monitor_classes
from .version import __version__, __git_version__


def main():
    parser = argparse.ArgumentParser(
        description='Monitoring of the system resources')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument('--git-version', action='version',
                        version='%(prog)s {version}'.format(version=__git_version__))
    sp = parser.add_subparsers(dest='command')
    sp.required = True
    sp_collect = sp.add_parser('collect', help='Collect system data.')
    sp_collect.add_argument('--time_interval', '-t', type=int, default=60,
                            help='Period of the measures, in seconds.')
    sp_collect.add_argument('targets', nargs='+', help='what to collect', choices=['all', 'cpu_stats', 'cpu_freq',
                                                                       'cpu_load', 'memory_usage', 'temperature', 'network'])
    sp_collect.add_argument('output_file', type=argparse.FileType('w'),
                            help='Output file for the measures.')
    sp_collect = sp.add_parser('plot', help='Plot the collected data.')
    sp_collect.add_argument('input_file', type=argparse.FileType('r'),
                            help='Input file of the measures.')
    sp_collect.add_argument('column_name', type=str, nargs='*',
                            help='Columns to plot.')
    sp_collect = sp.add_parser('merge', help='Merge the given CSV files.')
    sp_collect.add_argument('input_file', type=argparse.FileType('r'), nargs='+',
                            help='Input files to merge.')
    sp_collect.add_argument('output_file', type=str,
                            help='Output file to store the merged data.')
    args = parser.parse_args(sys.argv[1:])
    if args.command == 'collect':
        if 'all' in args.targets:
            to_monitor = monitor_classes.values()
        else:
            to_monitor = set()
            for target in args.targets:
                to_monitor.add(monitor_classes[target])

        monitor = Monitor([mon() for mon in to_monitor], time_interval=args.time_interval,
                          output_file=args.output_file)
        t = time.time()
        monitor.start_loop()
        t = time.time() - t
        print('Monitored the sytem for %d seconds' % int(t))
    elif args.command == 'plot':
        try:
            drawer = Drawer(args.input_file)
            str(drawer.plot(args.column_name))
        except Exception as e:
            sys.exit(e)
    elif args.command == 'merge':
        dataframes = [pandas.read_csv(f) for f in args.input_file]
        pandas.concat(dataframes, sort=False).to_csv(args.output_file, index=False)
    else:
        assert False


if __name__ == '__main__':
    main()
