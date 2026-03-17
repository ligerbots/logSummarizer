#!/usr/bin/python3

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

        if self.point_type == 'current':
            self.amp_hours = 0.0
            self.watts_hours = 0.0

        return

    def update(self, timestamp, value, enabled, voltage=12.0):
        if value == self.prev_value:
            return
        if self._while_enabled and not enabled and self.point_type != 'brownout':
            self.prev_value = None
            return

        self.count += 1
        self._total += value
        if self.min is None or value < self.min:
            self.min = value
        if self.max is None or value > self.max:
            self.max = value

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
            return self._total / self.count if self.count > 0 else 0.0
        elif key == 'time_avg':
            return self.integral / self.total_time if self.total_time > 0 else 0.0
        raise AttributeError(f"{self.__class__.__name__} has no attribute {key}")

    def __str__(self):
        if self.point_type == 'current':
            return f"avg={self.avg:.3f} max={self.max:.3f} amp_hrs={self.amp_hours:.3f} watts_hrs={self.watts_hours:.3f}"
        elif self.point_type == 'time':
            return f"total_time={self.total_time:.3f}"
        elif self.point_type == 'voltage':
            return f"mean={self.avg:.3f} min={self.min:.3f}"
        elif self.point_type == 'brownout':
            return f"total_time={self.integral:.3f}"
        return f"mean={self.avg:.3f} max={self.max:.3f} time_avg={self.time_avg:.3f}"
