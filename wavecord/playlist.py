# SPDX-License-Identifier: MIT
"""Playlist model for Lavalink playlist load results."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Iterator, List, Optional, Any

from .track import Track

if TYPE_CHECKING:
    from .typings import PlaylistInfo, TrackData

__all__ = ("Playlist",)


class Playlist:
    r"""Represents a Lavalink playlist load result.

    Attributes
    ----------
    name : str
        The name of the playlist.
    tracks : list[:class:`Track`]
        All tracks in the playlist, in order.
    selected_track : :class:`Track` or None
        The track that was selected when the URL was loaded (e.g. via a
        YouTube timestamp link), or ``None``.
    plugin_info : dict
        Raw plugin-specific metadata, if any.
    """

    __slots__ = ("name", "plugin_info", "selected_track", "tracks")

    def __init__(
        self,
        *,
        info: PlaylistInfo,
        tracks: List[TrackData],
        plugin_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name: str = info.get("name", "Unknown Playlist")
        self.plugin_info: Dict[str, Any] = plugin_info or {}

        self.tracks: List[Track] = [Track.from_data(t) for t in tracks]

        selected_index: int = info.get("selectedTrack", -1)
        self.selected_track: Optional[Track] = (
            self.tracks[selected_index]
            if 0 <= selected_index < len(self.tracks)
            else None
        )

    # Dunder helpers
    def __len__(self) -> int:
        return len(self.tracks)

    def __iter__(self) -> Iterator[Track]:
        return iter(self.tracks)

    def __repr__(self) -> str:
        return (
            f"<Playlist name={self.name!r} "
            f"tracks={len(self.tracks)} "
            f"selected={self.selected_track!r}>"
        )
