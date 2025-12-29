from datetime import time
from pathlib import Path


def seconds_to_time(seconds: float) -> time:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    # f"{h:02}:{m:02}:{s:02},{ms:03}"
    return time(
        hour=h, minute=m, second=s, microsecond=ms * 1000
    )  # Convert milliseconds to microseconds


def time_to_seconds(t: time) -> float:
    """Convert time object to total seconds."""
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1_000_000


class FileWriter:
    @staticmethod
    def write(path: str | Path, content: str):
        if isinstance(path, str):
            path = Path(path)

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(content)
