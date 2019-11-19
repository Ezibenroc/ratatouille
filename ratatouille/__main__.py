import argparse
import time
import sys
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
    sp_collect.add_argument('output_file', type=argparse.FileType('w'),
                            help='Output file for the measures.')
    sp_collect = sp.add_parser('plot', help='Plot the collected data.')
    sp_collect.add_argument('input_file', type=argparse.FileType('r'),
                            help='Input file of the measures.')
    args = parser.parse_args(sys.argv[1:])
    if args.command == 'collect':
        monitor = Monitor(monitor_classes, time_interval=args.time_interval,
                          output_file=args.output_file)
        t = time.time()
        monitor.start_loop()
        t = time.time() - t
        print('Monitored the sytem for %d seconds' % int(t))
    elif args.command == 'plot':
        drawer = Drawer(args.input_file)
        str(drawer.plot())
    else:
        assert False


if __name__ == '__main__':
    main()
