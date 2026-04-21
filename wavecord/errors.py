# SPDX-License-Identifier: MIT
"""All exceptions raised by WaveCord."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .typings import ExceptionPayload

__all__ = (
    "WavecordError",
    # Library
    "NoCompatibleLibraries",
    "MultipleCompatibleLibraries",
    # Node
    "NodeAlreadyConnected",
    "NodeNotConnected",
    "NodeAlreadyExists",
    # Pool
    "NoNodesAvailable",
    # Player
    "PlayerNotConnected",
    # Track
    "TrackLoadException",
    # HTTP
    "HTTPException",
    "HTTPBadRequest",
    "HTTPUnauthorized",
    "HTTPNotFound",
)


# Base
class WavecordError(Exception):
    """Base class for all WaveCord exceptions."""


# Library detection
class NoCompatibleLibraries(WavecordError):
    """Raised when no compatible Discord library is installed.

    Install one of: ``discord.py``, ``nextcord``, ``disnake``, or ``py-cord``.
    """

    def __init__(self) -> None:
        super().__init__(
            "No compatible Discord library was found. "
            "Please install one of: discord.py, nextcord, disnake, py-cord."
        )


class MultipleCompatibleLibraries(WavecordError):
    """Raised when more than one compatible Discord library is installed.

    Parameters
    ----------
    found : list[str]
        The libraries that were detected.
    """

    def __init__(self, found: list[str]) -> None:
        self.found = found
        super().__init__(
            f"Multiple compatible Discord libraries were found: {', '.join(found)}. "
            "Please uninstall all but one, or set the WAVECORD_IGNORE_LIBRARY_CHECK "
            "environment variable."
        )


# Node
class NodeAlreadyConnected(WavecordError):
    """Raised when attempting to connect a node that is already connected."""

    def __init__(self) -> None:
        super().__init__("This node is already connected.")


class NodeNotConnected(WavecordError):
    """Raised when an operation requires the node to be connected but it is not.

    Parameters
    ----------
    label : str
        The label of the node.
    """

    def __init__(self, label: str = "unknown") -> None:
        self.label = label
        super().__init__(f"Node '{label}' is not connected.")


class NodeAlreadyExists(WavecordError):
    """Raised when a node with the same label already exists in the pool.

    Parameters
    ----------
    label : str
        The conflicting label.
    """

    def __init__(self, label: str) -> None:
        self.label = label
        super().__init__(f"A node with the label '{label}' already exists in the pool.")


# Pool
class NoNodesAvailable(WavecordError):
    """Raised when no Lavalink nodes are available to handle a request."""

    def __init__(self) -> None:
        super().__init__(
            "No Lavalink nodes are currently available. "
            "Make sure at least one node is connected."
        )


# Player
class PlayerNotConnected(WavecordError):
    """Raised when an operation requires the player to be connected but it is not."""

    def __init__(self) -> None:
        super().__init__(
            "The player is not connected to a voice channel. "
            "Connect with channel.connect(cls=Player) first."
        )


# Track
class TrackLoadException(WavecordError):
    """Raised when Lavalink fails to load a track or playlist.

    Parameters
    ----------
    message : str
        The error message from Lavalink.
    severity : str
        The severity level (``common``, ``suspicious``, ``fault``).
    cause : str
        The root cause string from Lavalink.
    """

    def __init__(self, message: str, severity: str, cause: str) -> None:
        self.message = message
        self.severity = severity
        self.cause = cause
        super().__init__(f"[{severity.upper()}] Track load failed: {message} ({cause})")

    @classmethod
    def from_data(cls, data: ExceptionPayload) -> TrackLoadException:
        """Construct from a Lavalink exception payload.

        Parameters
        ----------
        data : ExceptionPayload
            The raw exception dict.
        """
        return cls(
            message=data.get("message", "Unknown error"),
            severity=data.get("severity", "fault"),
            cause=data.get("cause", ""),
        )


# HTTP
class HTTPException(WavecordError):
    """Raised when the Lavalink REST API returns a non-2xx status.

    Parameters
    ----------
    status : int
        The HTTP status code.
    message : str
        The response body text.
    """

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(f"HTTP {status}: {message}")


class HTTPBadRequest(HTTPException):
    """Raised for HTTP 400 Bad Request responses."""

    def __init__(self, message: str) -> None:
        super().__init__(400, message)


class HTTPUnauthorized(HTTPException):
    """Raised for HTTP 401 Unauthorized responses.

    This usually means the node password is wrong.
    """

    def __init__(self, message: str) -> None:
        super().__init__(401, message)


class HTTPNotFound(HTTPException):
    """Raised for HTTP 404 Not Found responses."""

    def __init__(self, message: str) -> None:
        super().__init__(404, message)
