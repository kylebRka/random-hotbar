"""Cancellable worker; all communication with Tk goes through a queue."""
import queue
import random
import threading
from .config import RunConfig, SPEEDS
from .selection import choose_key


class HotbarRunner:
    def __init__(self):
        self.events = queue.Queue()
        self._stop = threading.Event()
        self._thread = None

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self, config: RunConfig, backend):
        if self.running:
            return False
        # A fresh event per run prevents a rapid restart from reviving the old loop.
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._loop, args=(config, backend, self._stop), daemon=True
        )
        self._thread.start()
        return True

    def stop(self):
        self._stop.set()

    def _loop(self, config, backend, stop):
        try:
            if stop.wait(config.start_delay):
                return
            self.events.put(("started", None))
            while not stop.is_set():
                key = choose_key(config)
                backend.press(key)
                self.events.put(("key", key))
                if stop.wait(random.uniform(*SPEEDS[config.speed])):
                    break
        except Exception as error:
            self.events.put(("error", str(error)))
        finally:
            self.events.put(("stopped", None))
