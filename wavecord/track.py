# SPDX-License-Identifier: MIT
"""Track model representing a Lavalink audio track."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .typings import TrackData, TrackInfo, TrackWithInfo

__all__ = ("Track",)


class Track:
    r"""Represents a single Lavalink audio track.

    .. note::

        Do not instantiate this directly. Use :meth:`from_data` or
        :meth:`from_data_with_info`.

    Attributes
    ----------
    id : str
        The base64-encoded track string used internally by Lavalink.
    identifier : str
        The platform-specific identifier (e.g. a YouTube video ID).
    title : str
        The track title.
    author : str
        The uploader or artist name.
    length : int
        Total duration in milliseconds.
    uri : str or None
        Direct URL to the track, if available.
    source : str
        Source name as reported by Lavalink (e.g. ``youtube``).
    is_stream : bool
        Whether this track is a live stream.
    is_seekable : bool
        Whether seeking is supported for this track.
    artwork_url : str or None
        URL to the track thumbnail or artwork, if available.
    isrc : str or None
        International Standard Recording Code, if available.
    position : int
        Playback start position in milliseconds, usually ``0``.
    """

    __slots__ = (
        "_info",
        "artwork_url",
        "author",
        "id",
        "identifier",
        "is_seekable",
        "is_stream",
        "isrc",
        "length",
        "position",
        "source",
        "title",
        "uri",
    )

    def __init__(self, *, id: str, info: TrackInfo) -> None:
        self.id: str = id
        self._info: TrackInfo = info

        self.identifier: str = info["identifier"]
        self.title: str = info["title"]
        self.author: str = info["author"]
        self.length: int = info["length"]
        self.uri: Optional[str] = info.get("uri")
        self.source: str = info["sourceName"]
        self.is_stream: bool = info["isStream"]
        self.is_seekable: bool = info["isSeekable"]
        self.artwork_url: Optional[str] = info.get("artworkUrl")
        self.isrc: Optional[str] = info.get("isrc")
        self.position: int = info.get("position", 0)

    # Constructors
    @classmethod
    def from_data(cls, data: TrackData) -> Track:
        """Construct a :class:`Track` from a full Lavalink v4 track payload.

        Parameters
        ----------
        data : TrackData
            The raw track dict (with ``encoded`` and ``info`` keys).

        Returns
        -------
        Track
        """
        return cls(id=data["encoded"], info=data["info"])

    @classmethod
    def from_data_with_info(cls, data: TrackWithInfo) -> Track:
        """Alias for :meth:`from_data` for clarity when the payload includes info.

        Parameters
        ----------
        data : TrackWithInfo

        Returns
        -------
        Track
        """
        return cls.from_data(data)

    # Properties
    @property
    def duration(self) -> float:
        """Total duration in seconds (convenience wrapper around :attr:`length`)."""
        return self.length / 1000

    # Dunder methods
    def __str__(self) -> str:
        return f"{self.title} by {self.author}"

    def __repr__(self) -> str:
        return (
            f"<Track title={self.title!r} "
            f"author={self.author!r} "
            f"source={self.source!r} "
            f"length={self.length}ms "
            f"stream={self.is_stream}>"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Track):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
