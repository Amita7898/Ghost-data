"""Single-backend ownership of a SQLite data directory; no distributed queue."""

import os
from contextlib import contextmanager


@contextmanager
def exclusive_file(path):
    with path.open("a+b") as lock:
        try:
            if os.name == "nt":
                import msvcrt

                if path.stat().st_size == 0:
                    lock.write(b"0")
                    lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RuntimeError(
                "Another API owns this data directory; use one backend worker"
            ) from None
        try:
            yield
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)
