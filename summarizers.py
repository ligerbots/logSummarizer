#!/usr/bin/python3

import sys
import re
from lib.value_summary import ValueSummary


class Summarizer:
    def __init__(self, filename, filetype, enabled_only=True):
        self.filename = filename
        self.filetype = filetype
        self.enabled_only = enabled_only
        self.point_summaries = {}
        self.timestamp_name = None

        if filetype == 'dslog':
            self.enabled_func = Summarizer.dslogEnabled
        elif filetype == 'hoot':
            self.enabled_func = Summarizer.hootEnabled
        else:
            print("Unsupported filetype", filetype, file=sys.stderr)
            sys.exit(12)

        self.values = []
        return

    @staticmethod
    def dslogEnabled(event):
        disabled = event.get('ds_disabled', None)
        return not disabled if disabled is not None else None

    @staticmethod
    def hootEnabled(event):
        return event.get('RobotEnable', None)

    def check_new_columns(self, events):
        return

    def read_file(self, reader) -> None:
        numcols = 0
        rows_read = 0
        for event in reader:
            nc = len(event)
            if nc > numcols:
                self.check_new_columns(event)
                numcols = nc
            
            timestamp = event[self.timestamp_name]
            enabled = self.enabled_func(event)
            if self.enabled_only and enabled is None:
                # if enabled is not defined, skip. Otherwise, let the summarizer decide
                continue

            for point_name, summary_type in self.values:
                value = event.get(point_name, None)
                if value is None:
                    continue

                if isinstance(value, list):
                    # value is an array
                    for index, element in enumerate(value):
                        element_name = f"{point_name}[{index}]"
                        summary = self.point_summaries.setdefault(element_name, ValueSummary(summary_type, self.enabled_only))
                        summary.update(timestamp, element, enabled)
                else:
                    summary = self.point_summaries.setdefault(point_name, ValueSummary(summary_type, self.enabled_only))
                    summary.update(timestamp, value, enabled)

            rows_read += 1
            if rows_read % 1000 == 0:
                print(f"{rows_read} rows", file=sys.stderr, end="\r")
        return

    def print_summary(self) -> None:
        for point, summary in sorted(self.point_summaries.items()):
            print(f"{point}: {summary}")
        return

    def summary_value(self, key):
        return self.point_summaries.get(key, None)


class DsLogSummarizer(Summarizer):
    def __init__(self, filename, filetype, enabled_only):
        super().__init__(filename, filetype, enabled_only)
        self.timestamp_name = 'file_time'
        self.values = [
            ('round_trip_time', 'number'),
            ('can_usage', 'number'),
            ('packet_loss', 'number'),
            ('voltage', 'voltage'),
            ('brownout', 'fault'),
            ('pd_currents', 'current'),
            ('pd_total_current', 'current'),
        ]
        self.enabled_func = DsLogSummarizer.enabled

        self.drive_motors_pd = (9, 7, 15, 16)
        self.steer_motors_pd = (8, 12, 17, 2)
        self.fly_motors_pd = (18, 19)
        self.feed_motors_pd = (0, 3)
        self.intake_motors_pd = (6,)
        return

    def print_summary(self):
        super().print_summary()

        print()
        tot_ah = sum([self.summary_value(f'pd_currents[{chan}]').amp_hours for chan in self.drive_motors_pd])
        print(f'drive motors:  {tot_ah:.3f} Ah')
        tot_ah = sum([self.summary_value(f'pd_currents[{chan}]').amp_hours for chan in self.steer_motors_pd])
        print(f'steer motors:  {tot_ah:.3f} Ah')
        tot_ah = sum([self.summary_value(f'pd_currents[{chan}]').amp_hours for chan in self.fly_motors_pd])
        print(f'fly motors:   {tot_ah:.3f} Ah')
        tot_ah = sum([self.summary_value(f'pd_currents[{chan}]').amp_hours for chan in self.feed_motors_pd])
        print(f'feed motors:  {tot_ah:.3f} Ah')
        tot_ah = sum([self.summary_value(f'pd_currents[{chan}]').amp_hours for chan in self.intake_motors_pd])
        print(f'intake motor:  {tot_ah:.3f} Ah')
        return
    

class HootCurrentSummarizer(Summarizer):
    MAX_CAN_ID = 30
    def __init__(self, filename, filetype, enabled_only):
        super().__init__(filename, filetype, enabled_only)
        self.timestamp_name = 'timestamp'

        # currents
        self.device_type = 'TalonFX'
        self.supply_current = 'SupplyCurrent'
        self.stator_current = 'StatorCurrent'

        self.values = []
        # just add call CAN IDs, extras won't be found, so will be ignored
        for canid in range(1, self.MAX_CAN_ID):
            self.values.append((f'Phoenix6/{self.device_type}-{canid}/{self.supply_current}', 'current'))
            self.values.append((f'Phoenix6/{self.device_type}-{canid}/{self.stator_current}', 'current'))

        self.drive_motors_can = (1, 3, 5, 7)
        self.steer_motors_can = (2, 4, 6, 8)
        self.fly_motors_can = (9, 10)
        self.feed_motors_can = (18, 22)
        self.intake_motors_can = (17,)
        return

    def print_summary(self):
        print(','.join(('Filename', 'Property', 'Value')))

        for canid in range(1, self.MAX_CAN_ID):
            for prop in (self.supply_current, self.stator_current):
                name = f'Phoenix6/{self.device_type}-{canid}/{prop}'
                val = self.summary_value(name)
                if val is not None:
                    print(','.join((self.filename, name + '.max', str(val.max))))
                    print(','.join((self.filename, name + '.percent95', str(val.percent95))))
        return
    

class FaultSummarizer(Summarizer):
    def __init__(self, filename, filetype, enabled_only):
        super().__init__(filename, filetype, enabled_only)
        self.timestamp_name = 'timestamp'

        self.columns_added = set()
        return

    def check_new_columns(self, events):
        for col in events.keys():
            if col not in self.columns_added and re.search(r"/(Sticky)?Fault_", col):
                self.values.append((col, 'fault'))
                self.columns_added.add(col)
        return

    @staticmethod
    def enabled(event):
        return event.get('RobotEnable', None)

    def print_summary(self) -> None:
        print("Faults found:")
        for point, summary in sorted(self.point_summaries.items()):
            tt = summary.max
            if tt > 0:
                print(f"{point}: {summary}")
        return
