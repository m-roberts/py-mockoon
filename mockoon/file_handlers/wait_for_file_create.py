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
