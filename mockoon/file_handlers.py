from logging import getLogger
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = getLogger(__name__)


class WaitForFileCreationHandler(FileSystemEventHandler):
    """Event handler that stops an observer when a specific file is created."""

    def __init__(self, observer: Observer, target_file: Path) -> None:
        """Initialize a new WaitForFileCreationHandler instance.

        Parameters
        ----------
        observer (Observer): The observer to stop when the target file is created.
        target_file (Path): The file to watch for creation.
        """
        self.observer = observer
        self.target_file = target_file

    def on_created(self, event):
        """Handle the file creation event."""
        if str(event.src_path) == str(self.target_file):
            logger.info(f"{self.target_file} has been created.")
            self.observer.stop()


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
