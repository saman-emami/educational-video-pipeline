from __future__ import annotations

import logging
import time
from typing import Optional

from tqdm.auto import tqdm


class ProgressTracker:
    """
    Lightweight wrapper around tqdm for CLI progress indication.
    """

    def __init__(self) -> None:
        self._bar: Optional[tqdm] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    def start(self, description: str) -> None:
        """Initialize progress bar."""
        if self._bar is not None:
            self._bar.close()
        self._bar = tqdm(total=100, desc=description, ncols=100)
        self._bar.update(0)

    # ------------------------------------------------------------------ #
    def update(self, percent: float, note: str = "") -> None:
        """
        Increment bar to a new absolute percentage.
        """
        if self._bar is None:
            self.start("Working")
        percent = min(max(percent, 0), 100)
        self._bar.n = percent
        self._bar.set_postfix_str(note)
        self._bar.refresh()

    # ------------------------------------------------------------------ #
    def finish(self, final_note: str = "Done") -> None:
        """Complete and close the bar."""
        if self._bar:
            self._bar.n = 100
            self._bar.set_postfix_str(final_note)
            self._bar.refresh()
            time.sleep(0.1)
            self._bar.close()
            self._bar = None
