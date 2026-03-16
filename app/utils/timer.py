# # app/utils/timer.py

import time

class Timer:

    def __init__(self):
        self.start = time.perf_counter()
        self.last = self.start

    def step(self, name: str):
        now = time.perf_counter()
        diff = now - self.last
        print(f"⏱ {name}: {diff:.3f}s")
        self.last = now

    def total(self):
        total = time.perf_counter() - self.start
        print(f"⏱ TOTAL: {total:.3f}s")