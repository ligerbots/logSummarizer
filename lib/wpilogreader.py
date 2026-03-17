#!/usr/bin/python3

from datetime import datetime
import mmap

from . import datalog


class WpilogReader:
    def __init__(self, filename: str):
        self.logreader = None
        self.open(filename)
        return

    def open(self, filename) -> None:
        self.strm = open(filename, "r")
        self.mm = mmap.mmap(self.strm.fileno(), 0, access=mmap.ACCESS_READ)
        self.logreader = datalog.DataLogReader(self.mm)
        if not self.logreader:
            raise Exception(f'{filename} is not a wpilog file')
        return

    def close(self) -> None:
        if self.mm:
            self.mm.close()
        if self.logreader:
            self.logreader.close()
        if self.strm:
            self.strm.close()
        return

    def __iter__(self):
        entries = {}
        values = {}
        prev_timestamp = None

        for record in self.logreader:
            values['timestamp'] = record.timestamp / 1000000.0

            if record.isStart():
                data = record.getStartData()
                entries[data.entry] = data
            elif record.isFinish():
                entry = record.getFinishEntry()
                if entry in entries:
                    del entries[entry]
            elif record.isSetMetadata():
                # not used?
                pass
            elif record.isControl():
                pass
            else:
                entry = entries.get(record.entry, None)
                if entry is None:
                    continue
                entry_name = entry.name

                try:
                    # handle systemTime specially
                    if entry_name == "systemTime" and entry.type == "int64":
                        dt = datetime.fromtimestamp(record.getInteger() / 1000000)
                        values[entry_name] = dt
                    elif entry.type == "double":
                        values[entry_name] = record.getDouble()
                    elif entry.type == "int64":
                        values[entry_name] = record.getInteger()
                    elif entry.type in ("string", "json"):
                        values[entry_name] = record.getString()
                    elif entry.type == "msgpack":
                        values[entry_name] = record.getMsgPack()
                    elif entry.type == "boolean":
                        values[entry_name] = record.getBoolean()
                    elif entry.type == "boolean[]":
                        values[entry_name] = record.getBooleanArray()
                    elif entry.type == "double[]":
                        values[entry_name] = record.getDoubleArray()
                    elif entry.type == "float[]":
                        values[entry_name] = record.getFloatArray()
                    elif entry.type == "int64[]":
                        values[entry_name] = record.getIntegerArray()
                    elif entry.type == "string[]":
                        values[entry_name] = record.getStringArray()
                except TypeError:
                    raise Exception(f"Unknown type {entry.type} for entry {entry_name}")

            if values['timestamp'] != prev_timestamp:
                yield values
                prev_timestamp = values['timestamp']

        return


# Test routine
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: wpilogreader.py <filename> [<entryname>]")
        sys.exit(1)

    filename = sys.argv[1]
    reader = WpilogReader(filename)

    entryname = sys.argv[2] if len(sys.argv) > 2 else None

    for record in reader:
        if entryname is None:
            print(record)
        else:
            value = record.get(entryname, None)
            if value is not None:
                print(f"{record['timestamp']}: {entryname} = {value}")

    reader.close()
    