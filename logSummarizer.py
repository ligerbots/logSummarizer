#!/usr/bin/env python3

import argparse
import re
import sys

# import dslogparser
# from lib import hootreader
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


# def summarize_file(reader, config, enabled_only) -> None:
#     point_summaries = {}

#     for event in reader:
#         timestamp = event[config['timestamp']]
#         if "enabled" in config:
#             enabled = event.get(config['enabled'], None)
#         elif "disabled" in config:
#             disabled = event.get(config['disabled'], None)
#             enabled = not disabled if disabled is not None else None
#         else:
#             raise Exception("Must specify either enabled or disabled in values")
#         if enabled_only and enabled is None:
#             # if enabled is not defined, skip. Otherwise, let the summarizer decide
#             continue

#         for point_name, summary_type in config['values']:
#             value = event.get(point_name, None)
#             if value is None:
#                 continue

#             if isinstance(value, list):
#                 # value is an array
#                 for index, element in enumerate(value):
#                     element_name = f"{point_name}[{index}]"
#                     summary = point_summaries.setdefault(element_name, ValueSummary(summary_type, enabled_only))
#                     summary.update(timestamp, element, enabled)
#             else:
#                 summary = point_summaries.setdefault(point_name, ValueSummary(summary_type, enabled_only))
#                 summary.update(timestamp, value, enabled)

#     for point, summary in sorted(point_summaries.items()):
#         print(f"{point}: {summary}")
#     return


def main() -> None:
    parser = argparse.ArgumentParser(description='Summarize match log file')
    parser.add_argument('--filetype', '-t', choices=['dslog', 'event', 'hoot', 'wpilog', 'faults'], default='dslog', help='Type of input file')
    parser.add_argument('--all-time', '-A', action='store_true', help='Include all points, not just enabled')
    parser.add_argument('--list', '-l', action='store_true', help='List all point in the log and exit')
    parser.add_argument('--verbose', '-v', action='count', help='Increase verbosity level')
    parser.add_argument('file', nargs=1, help='Input file')

    args = parser.parse_args()

    reader = None
    summarizer = None

    try:
        if args.filetype == 'wpilog':
            reader = wpilogreader.WpilogReader(args.file[0])
            values = WPILOG_VALUES
        elif args.filetype == 'dslog':
            reader = dslogparser.DSLogParser(args.file[0])
            summarizer = summarizers.DsLogSummarizer(not args.all_time, args.file[0])
        elif args.filetype == 'hoot':
            reader = hootreader.HootReader(args.file[0])
            summarizer = summarizers.HootSummarizer(not args.all_time, args.file[0])
        elif args.filetype == 'faults':
            reader = hootreader.HootReader(args.file[0])
            summarizer = summarizers.CTRFaultSummarizer(False, args.file[0])
        else:
            print(f"Unsupported file type: {args.filetype}")
            sys.exit(1)

        if args.list:
            list_points(reader)
        else:
            summarizer.read_file(reader)
            summarizer.print_summary()
    finally:
        if reader is not None:
            reader.close()


main()
