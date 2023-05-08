from logging import getLogger
from pathlib import Path

from watchdog.events import FileSystemEventHandler

logger = getLogger(__name__)


class LogFileEventHandler(FileSystemEventHandler):
    """Event handler for processing log files."""

    def __init__(self, callback, target_file: Path) -> None:
        """Initialize a new LogFileEventHandler instance.

        Parameters
        ----------
        callback (callable): The function to call when processing a log line.
        target_file (Path): The log file to watch for changes.
        """
        self.callback = callback
        self.target_file = target_file

    def initial_read(self):
        """Read and process the initial content of the log file."""
        with self.target_file.open() as file:
            content = file.readlines()
            for line in content:
                self.callback(line)

    def on_modified(self, event):
        """Handle the file modification event."""
        if str(event.src_path) == str(self.target_file):
            with Path(event.src_path).open() as file:
                content = file.readlines()
                for line in content[-1:]:
                    self.callback(line)
