import argparse
import time
import sys
from .ratatouille import Monitor, Drawer, monitor_classes, merge_files, RatatouilleDependencyError
from .ratatouille import RatatouillePortabilityError
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
    sp_collect.add_argument('targets', nargs='+', help='what to collect', choices=list(monitor_classes) + ['all'])
    sp_collect.add_argument('output_file', type=argparse.FileType('w'),
                            help='Output file for the measures.')
    sp_collect = sp.add_parser('plot', help='Plot the collected data.')
    sp_collect.add_argument('input_file', type=argparse.FileType('r'),
                            help='Input file of the measures.')
    sp_collect.add_argument('--output', '-o', type=str,
                            help='Output file of the plot.')
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
        instances = []
        for mon in to_monitor:
            try:
                instances.append(mon())
            except RatatouillePortabilityError as e:
                sys.stderr.write('WARNING: %s\n' % e)
        monitor = Monitor([inst for inst in instances], time_interval=args.time_interval,
                          output_file=args.output_file)
        t = time.time()
        monitor.start_loop()
        t = time.time() - t
        print('Monitored the sytem for %d seconds' % int(t))
    elif args.command == 'plot':
        try:
            drawer = Drawer(args.input_file)
            plot = drawer.create_plot(args.column_name)
            if args.output:
                plot.save(args.output, dpi=300, height=13.35, width=25)
            else:
                str(plot)
        except Exception as e:
            sys.exit(e)
    elif args.command == 'merge':
        try:
            merge_files(args.input_file, args.output_file)
        except Exception as e:
            sys.exit(e)
    else:
        assert False


if __name__ == '__main__':
    main()
