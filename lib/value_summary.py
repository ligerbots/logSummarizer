#!/usr/bin/python3

import numpy


class ValueSummary:
    def __init__(self, point_type, while_enabled=False):
        self.point_type = point_type
        self._while_enabled = while_enabled
        self.prev_timestamp = None
        self.prev_value = None

        self.count = 0
        self._total = 0.0
        self.min = None
        self.max = None

        self.integral = 0.0
        self.total_time = 0.0

        self.values = None
        if self.point_type == 'current':
            self.amp_hours = 0.0
            self.watts_hours = 0.0

        if self.point_type in ('current', 'voltage'):
            self.values = []

        return

    def update(self, timestamp, value, enabled, voltage=12.0):
        if value == self.prev_value:
            return
        if self._while_enabled and not enabled and self.point_type != 'fault':
            self.prev_value = None
            return

        self.count += 1
        self._total += value
        if self.min is None or value < self.min:
            self.min = value
        if self.max is None or value > self.max:
            self.max = value

        if self.values is not None:
            self.values.append(value)

        if self.prev_timestamp is not None and self.prev_value is not None:
            dt = timestamp - self.prev_timestamp
            self.total_time += dt
            self.integral += self.prev_value * dt

            if self.point_type == 'current':
                dt_hours = dt / 3600.0
                self.amp_hours += abs(self.prev_value) * dt_hours
                self.watts_hours += abs(self.prev_value * voltage) * dt_hours

        self.prev_timestamp = timestamp
        self.prev_value = value
        return

    def __getattr__(self, key):
        if key == 'avg':
            return self._total / self.count if self.count > 0 else None
        elif key == 'time_avg':
            return self.integral / self.total_time if self.total_time > 0 else None
        elif key == 'percent95':
            if self.values and len(self.values) > 3:
                return numpy.percentile(self.values, 95)
            return None
        elif key == 'percent5':
            if self.values and len(self.values) > 3:
                return numpy.percentile(self.values, 5)
            return None
        raise AttributeError(f"{self.__class__.__name__} has no attribute {key}")

    def __str__(self):
        if self.point_type == 'current':
            res = f"avg={self.avg:.2f} max={self.max:.2f} Ah={self.amp_hours:.3f} Wh={self.watts_hours:.2f}"
            p95 = self.percent95
            if p95 is not None:
                res += f" 95pct={p95:.2f}"
            return res
        elif self.point_type == 'time':
            return f"total_time={self.total_time:.2f}"
        elif self.point_type == 'voltage':
            res = f"mean={self.avg:.2f} min={self.min:.2f}"
            p5 = self.percent5
            if p5 is not None:
                res += f" 5pct={p5:.2f}"
            return res
        elif self.point_type == 'fault':
            return f"max={self.max} total_time={self.integral:.2f}"

        return f"mean={self.avg:.2f} max={self.max:.2f} time_avg={self.time_avg:.2f}"
