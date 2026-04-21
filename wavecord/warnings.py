# SPDX-License-Identifier: MIT
"""Custom warnings emitted by WaveCord."""

from __future__ import annotations

__all__ = ("UnsupportedVersionWarning", "UnknownVersionWarning")


class UnsupportedVersionWarning(UserWarning):
    """Emitted when the connected Lavalink version is newer than what WaveCord was tested against.

    Some features may not work correctly.
    """

    message = (
        "The connected Lavalink version is newer than what WaveCord was tested against. "
        "Some features may not behave as expected. Please open an issue if you "
        "encounter problems."
    )


class UnknownVersionWarning(UserWarning):
    """Emitted when WaveCord cannot parse the Lavalink version string.

    This can happen with development builds or custom forks.
    """

    message = (
        "WaveCord could not determine the Lavalink version. "
        "Assuming 3.7.x compatibility. Some features may not work correctly."
    )
