# # app/utils/timer.py
# import time
# import logging
# import inspect

# logger = logging.getLogger("cropeye-timer")

# def timer(name: str):
#     def decorator(func):

#         if inspect.iscoroutinefunction(func):

#             async def async_wrapper(*args, **kwargs):
#                 start = time.perf_counter()
#                 result = await func(*args, **kwargs)
#                 duration = time.perf_counter() - start
#                 # logger.info(f"⏱ {name} took {duration:.3f}s")
#                 logger.info(f"⏱ {name} took {duration*1000:.2f} ms")
#                 return result

#             return async_wrapper

#         else:

#             def sync_wrapper(*args, **kwargs):
#                 start = time.perf_counter()
#                 result = func(*args, **kwargs)
#                 duration = time.perf_counter() - start
#                 logger.info(f"⏱ {name} took {duration:.3f}s")
#                 return result

#             return sync_wrapper

#     return decorator





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