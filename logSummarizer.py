#!/usr/bin/env python3

import argparse
import sys

# import dslogparser
# from lib import hootreader
from lib import wpilogreader
from lib.value_summary import ValueSummary


WPILOG_POINTS = [
    'NT:/SmartDashboard/shooterFeeder/supplyCurrent',
    'NT:/SmartDashboard/shooterFeeder/statorCurrent',
]


def main() -> None:
    parser = argparse.ArgumentParser(description='Summarize match log file')
    parser.add_argument('--filetype', '-t', choices=['dslog', 'event', 'hoot', 'wpilog'], default='dslog', help='Type of input file')
    parser.add_argument('--all-time', '-A', action='store_true', help='Include all points, not just enabled')
    parser.add_argument('--verbose', '-v', action='count', help='Increase verbosity level')
    parser.add_argument('file', nargs=1, help='Input file')

    args = parser.parse_args()

    if args.filetype == 'wpilog':
        reader = wpilogreader.WpilogReader(args.file[0])
        points = WPILOG_POINTS
    else:
        print(f"Unsupported file type: {args.filetype}")
        sys.exit(1)

    point_summaries = {}

    for event in reader:
        timestamp = event['timestamp']

        for point in points:
            enabled = event.get("DS:enabled", None)
            if enabled is None:
                continue

            value = event.get(point, None)
            if value is None:
                continue

            summary = point_summaries.setdefault(point, ValueSummary(not args.all_time))
            summary.update(timestamp, value, enabled)

    for point, summary in point_summaries.items():
        print(f"{point}: {summary}")


main()
