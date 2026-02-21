"""
File Watcher
--------------
Uses watchdog to monitor the sample_files folder in real-time.
Detects new / modified files and triggers the ingestion pipeline.
"""

import time
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from backend.utils.config import ALL_EXTENSIONS
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class LifeVaultFileHandler(FileSystemEventHandler):
    """
    Custom watchdog handler that triggers processing for supported file types.
    """

    def __init__(self, on_file_event: Callable[[str], None]):
        """
        Args:
            on_file_event: Callback function that receives an absolute file path
                           when a new or modified file is detected.
        """
        super().__init__()
        self.on_file_event = on_file_event

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle(event.src_path, "created")

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle(event.src_path, "modified")

    def _handle(self, file_path: str, event_type: str):
        """Only process supported file types."""
        ext = Path(file_path).suffix.lower()
        if ext in ALL_EXTENSIONS:
            logger.info(f"📁 File {event_type}: {file_path}")
            try:
                self.on_file_event(file_path)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        else:
            logger.debug(f"Skipping unsupported file: {file_path}")


class FileWatcher:
    """Manages the watchdog observer lifecycle."""

    def __init__(self, watch_folder: str, on_file_event: Callable[[str], None]):
        self.watch_folder = watch_folder
        self.handler = LifeVaultFileHandler(on_file_event)
        self.observer = Observer()

        # Ensure watch folder exists
        Path(watch_folder).mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start watching the folder (non-blocking)."""
        self.observer.schedule(self.handler, self.watch_folder, recursive=True)
        self.observer.daemon = True
        self.observer.start()
        logger.info(f"👁️ Watching folder: {self.watch_folder}")

    def stop(self):
        """Stop the file watcher."""
        self.observer.stop()
        self.observer.join()
        logger.info("File watcher stopped.")

    def scan_existing_files(self):
        """
        Scan all existing files in the folder on startup.
        This ensures files added while the app was offline are indexed.
        """
        folder = Path(self.watch_folder)
        count = 0
        for file_path in sorted(folder.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in ALL_EXTENSIONS:
                try:
                    self.handler.on_file_event(str(file_path))
                    count += 1
                except Exception as e:
                    logger.error(f"Error scanning {file_path}: {e}")

        logger.info(f"✓ Startup scan complete — processed {count} existing files.")
