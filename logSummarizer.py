#!/usr/bin/env python3

import argparse
import sys

# import dslogparser
# from lib import hootreader
from lib import hootreader, wpilogreader
from lib.value_summary import ValueSummary


WPILOG_VALUES = {
    'enabled': 'DS:enabled',
    'points': [
        'NT:/SmartDashboard/shooterFeeder/supplyCurrent',
        'NT:/SmartDashboard/shooterFeeder/statorCurrent'
    ]
}

HOOT_VALUES = {
    'enabled': 'RobotEnable',
    'points': [
        'Phoenix6/TalonFX-19/StatorCurrent',
        'Phoenix6/TalonFX-19/SupplyCurrent',
    ]
}


def list_points(reader) -> None:
    points = set()
    for event in reader:
        for key in event.keys():
            if key not in points:
                print(key)
                points.add(key)
    return


def summarize_file(reader, values, enabled_only) -> None:
    point_summaries = {}

    for event in reader:
        timestamp = event['timestamp']

        for point in values['points']:
            enabled = event.get(values['enabled'], None)
            if enabled is None:
                continue

            value = event.get(point, None)
            if value is None:
                continue

            summary = point_summaries.setdefault(point, ValueSummary(enabled_only))
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
