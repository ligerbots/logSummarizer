#!/usr/bin/env python3

import os.path
import argparse
import re
import sys

from lib import hootreader, wpilogreader, dslogparser
import summarizers


def list_points(reader) -> None:
    points = set()
    for event in reader:
        for key in event.keys():
            if key not in points:
                print(key)
                points.add(key)
    return


def main() -> None:
    parser = argparse.ArgumentParser(description='Summarize match log file')
    parser.add_argument('--report-type', '-t', choices=['dslog', 'event', 'currents', 'faults'], default='dslog', help='Type of input file')
    parser.add_argument('--all-time', '-A', action='store_true', help='Include all points, not just enabled')
    parser.add_argument('--list', '-l', action='store_true', help='List all point in the log and exit')
    parser.add_argument('--verbose', '-v', action='count', help='Increase verbosity level')
    parser.add_argument('file', nargs=1, help='Input file')

    args = parser.parse_args()

    reader = None
    summarizer = None

    fileext = os.path.splitext(args.file[0])[1][1:]

    try:
        if fileext == 'wpilog':
            reader = wpilogreader.WpilogReader(args.file[0])
        elif fileext in ('dslog', 'dsevent'):
            reader = dslogparser.DSLogParser(args.file[0])
        elif fileext == 'hoot':
            reader = hootreader.HootReader(args.file[0])
        else:
            print(f"Unsupported file type: {fileext}")
            sys.exit(1)

        if args.list:
            list_points(reader)
            sys.exit(0)
    
        # if args.report_type == 'wpilog':
        #     values = WPILOG_VALUES
        if args.report_type == 'dslog':
            summarizer = summarizers.DsLogSummarizer(args.file[0], fileext, not args.all_time)
        elif args.report_type == 'currents':
            summarizer = summarizers.HootCurrentSummarizer(args.file[0], fileext, not args.all_time)
        elif args.report_type == 'faults':
            summarizer = summarizers.FaultSummarizer(args.file[0], fileext, False)
        else:
            print(f"Unhandled report type: {args.report_type}")
            sys.exit(1)

        summarizer.read_file(reader)
        summarizer.print_summary()

    finally:
        if reader is not None:
            reader.close()
    return


main()
