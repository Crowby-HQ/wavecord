# SPDX-License-Identifier: MIT
"""Search source prefixes for Lavalink track loading."""

from __future__ import annotations

from enum import Enum

__all__ = ("SearchType",)


class SearchType(str, Enum):
    """Available search source prefixes.

    Pass one of these to :meth:`~wavecord.Player.fetch_tracks` (or
    :meth:`~wavecord.Node.fetch_tracks`) when searching by keyword rather
    than a direct URL.

    Examples
    --------
    .. code-block:: python

        results = await player.fetch_tracks(
            "never gonna give you up",
            SearchType.YOUTUBE,
        )

    Attributes
    ----------
    YOUTUBE
        Search YouTube (``ytsearch``).
    YOUTUBE_MUSIC
        Search YouTube Music (``ytmsearch``).
    SOUNDCLOUD
        Search SoundCloud (``scsearch``).
    SPOTIFY
        Search Spotify via a Lavalink plugin (``spsearch``).
    APPLE_MUSIC
        Search Apple Music via a Lavalink plugin (``amsearch``).
    DEEZER
        Search Deezer via a Lavalink plugin (``dzsearch``).
    YANDEX_MUSIC
        Search Yandex Music via a Lavalink plugin (``ymsearch``).
    """

    YOUTUBE = "ytsearch"
    YOUTUBE_MUSIC = "ytmsearch"
    SOUNDCLOUD = "scsearch"
    SPOTIFY = "spsearch"
    APPLE_MUSIC = "amsearch"
    DEEZER = "dzsearch"
    YANDEX_MUSIC = "ymsearch"
