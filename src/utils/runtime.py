import time
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def start_timer() -> float:
    return time.perf_counter()

def elapsed_seconds(start_time: float) -> float:
    return round(time.perf_counter() - start_time)

def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds into a human-readable string in the format "HH:MM:SS.sss".
    :param seconds: duration in seconds to format
    :return: a string representing the formatted duration
    """
    duration = []

    hours = int(seconds // 3600)
    if hours: duration.append(f"{hours:02d}:")

    minutes = int((seconds % 3600) // 60)
    if minutes: duration.append(f"{minutes:02d}:")

    secs = seconds % 60
    duration.append(f"{secs:06.3f}")

    return "".join(duration)