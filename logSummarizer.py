#!/usr/bin/env python3

import argparse
import sys

# import dslogparser
# from lib import hootreader
from lib import hootreader, wpilogreader, dslogparser
from lib.value_summary import ValueSummary


DSLOG_VALUES = {
    'disabled': 'ds_disabled',
    'timestamp': 'file_time',
    'events': None,
    'values': [
        ('round_trip_time', False, 'number'),
        ('can_usage', False, 'number'),
        ('packet_loss', False, 'number'),
        ('voltage', False, 'voltage'),
        ('brownout', False, 'brownout'),
        ('pd_currents', True, 'current'),
        ('pd_total_current', False, 'current'),
    ],
}

WPILOG_VALUES = {
    'enabled': 'DS:enabled',
    'timestamp': 'timestamp',
    'events': None,
    'values': [
        ('NT:/SmartDashboard/shooterFeeder/supplyCurrent', False, 'current'),
        ('NT:/SmartDashboard/shooterFeeder/statorCurrent', False, 'current'),
    ],
    'arrays': []
}

HOOT_VALUES = {
    'enabled': 'RobotEnable',
    'timestamp': 'timestamp',
    'events': None,
    'values': [
        ('Phoenix6/TalonFX-19/StatorCurrent', False, 'current'),
        ('Phoenix6/TalonFX-19/SupplyCurrent', False, 'current'),
    ],
}


def list_points(reader) -> None:
    points = set()
    for event in reader:
        for key in event.keys():
            if key not in points:
                print(key)
                points.add(key)
    return


def summarize_file(reader, config, enabled_only) -> None:
    point_summaries = {}

    for event in reader:
        timestamp = event[config['timestamp']]
        if "enabled" in config:
            enabled = event.get(config['enabled'], None)
        elif "disabled" in config:
            disabled = event.get(config['disabled'], None)
            enabled = not disabled if disabled is not None else None
        else:
            raise Exception("Must specify either enabled or disabled in values")
        if enabled_only and enabled is None:
            continue

        for vinfo in config['values']:
            point = vinfo[0]
            value = event.get(vinfo[0], None)
            if value is None:
                continue

            if vinfo[1]:   # array
                for index, element in enumerate(value):
                    point = f"{vinfo[0]}[{index}]"
                    summary = point_summaries.setdefault(point, ValueSummary(vinfo[2], enabled_only))
                    summary.update(timestamp, element, enabled)
            else:
                summary = point_summaries.setdefault(point, ValueSummary(vinfo[2], enabled_only))
                summary.update(timestamp, value, enabled)

    for point, summary in point_summaries.items():
        print(f"{point}: {summary}")
    return


def main() -> None:
    parser = argparse.ArgumentParser(description='Summarize match log file')
    parser.add_argument('--filetype', '-t', choices=['dslog', 'event', 'hoot', 'wpilog'], default='dslog', help='Type of input file')
    parser.add_argument('--all-time', '-A', action='store_true', help='Include all points, not just enabled')
    parser.add_argument('--list', '-l', action='store_true', help='List all point in the log and exit')
    parser.add_argument('--verbose', '-v', action='count', help='Increase verbosity level')
    parser.add_argument('file', nargs=1, help='Input file')

    args = parser.parse_args()

    reader = None

    try:
        if args.filetype == 'wpilog':
            reader = wpilogreader.WpilogReader(args.file[0])
            values = WPILOG_VALUES
        elif args.filetype == 'dslog':
            reader = dslogparser.DSLogParser(args.file[0])
            values = DSLOG_VALUES
        elif args.filetype == 'hoot':
            reader = hootreader.HootReader(args.file[0])
            values = HOOT_VALUES
        else:
            print(f"Unsupported file type: {args.filetype}")
            sys.exit(1)

        if args.list:
            list_points(reader)
        else:
            summarize_file(reader, values, not args.all_time)
    finally:
        if reader is not None:
            reader.close()


main()
