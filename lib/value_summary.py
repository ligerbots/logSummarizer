#!/usr/bin/python3

class ValueSummary:
    def __init__(self, while_enabled=False):
        self._while_enabled = while_enabled
        self.prev_timestamp = None
        self.prev_value = None

        self.count = 0
        self._total = 0.0
        self.max = None

        self.integral = 0.0
        self.total_time = 0.0

        return

    def update(self, timestamp, value, enabled):
        if value == self.prev_value:
            return
        if self._while_enabled and not enabled:
            self.prev_value = None
            return
        
        self.count += 1
        self._total += value
        if self.max is None or value > self.max:
            self.max = value

        if self.prev_timestamp is not None and self.prev_value is not None:
            dt = timestamp - self.prev_timestamp
            self.total_time += dt
            self.integral += self.prev_value * dt

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
        return f"mean={self.avg:.3f}, max={self.max}, integral={self.integral:.3f}, time_avg={self.time_avg:.3f}"