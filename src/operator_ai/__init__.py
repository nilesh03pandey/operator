from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("operator-ai")
except PackageNotFoundError:
    # Source tree usage before installation/editable install.
    __version__ = "0.0.0"
