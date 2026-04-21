# SPDX-License-Identifier: MIT
# ruff: noqa: PGH003
"""Multi-library compatibility layer for discord.py, nextcord, disnake and py-cord."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from os import getenv
from typing import TYPE_CHECKING, Any

from .errors import MultipleCompatibleLibraries

__all__ = (
    "Client",
    "Connectable",
    "ExponentialBackoff",
    "Guild",
    "GuildChannel",
    "GuildVoiceStatePayload",
    "MISSING",
    "StageChannel",
    "VoiceChannel",
    "VoiceProtocol",
    "VoiceServerUpdatePayload",
    "dumps",
    "loads",
    "version_info",
)

# Library detection
_SUPPORTED = ("nextcord", "disnake", "py-cord", "discord.py", "discord")
_found: list[str] = []

for _lib in _SUPPORTED:
    try:
        version(_lib)
    except PackageNotFoundError:
        pass
    else:
        _found.append(_lib)

if not getenv("WAVECORD_IGNORE_LIBRARY_CHECK"):
    if len(_found) == 0:
        class _MissingType:
            """Placeholder type used when no Discord library is installed."""

        Client = Guild = StageChannel = VoiceChannel = VoiceProtocol = _MissingType
        Connectable = GuildChannel = ExponentialBackoff = _MissingType
        MISSING = object()
        version_info = None

        if TYPE_CHECKING:
            GuildVoiceStatePayload = dict[str, Any]
            VoiceServerUpdatePayload = dict[str, Any]

    elif len(_found) > 1:
        raise MultipleCompatibleLibraries(_found)

    else:
        # nextcord spams RuntimeWarning on import — suppress it
        if _found[0] == "nextcord":
            from warnings import simplefilter

            simplefilter("ignore", RuntimeWarning)
            try:
                from nextcord.health_check import DistributionWarning  # type: ignore
            except ImportError:
                pass
            else:
                simplefilter("ignore", DistributionWarning)  # type: ignore[arg-type]
            finally:
                simplefilter("always", RuntimeWarning)

        _library = _found[0]

        # Version check
        if _library == "nextcord":
            from nextcord import version_info
        elif _library == "disnake":
            from disnake import version_info
        else:
            from discord import version_info

        if _library == "nextcord":
            if version_info.major not in (2, 3):
                raise RuntimeError("WaveCord requires nextcord version 2 or 3.")
        elif version_info.major != 2:
            raise RuntimeError(f"WaveCord requires version 2 of {_library}.")

        # Imports by library
        if _library == "nextcord":
            from nextcord import (
                Client,
                Guild,
                StageChannel,
                VoiceChannel,
                VoiceProtocol,
                version_info,
            )
            from nextcord.abc import Connectable, GuildChannel
            from nextcord.backoff import ExponentialBackoff
            from nextcord.utils import MISSING

            if TYPE_CHECKING:
                from nextcord.types.voice import (
                    GuildVoiceState as GuildVoiceStatePayload,
                    VoiceServerUpdate as VoiceServerUpdatePayload,
                )

        elif _library == "disnake":
            from disnake import (
                Client,
                Guild,
                StageChannel,
                VoiceChannel,
                VoiceProtocol,
                version_info,
            )
            from disnake.abc import Connectable, GuildChannel
            from disnake.backoff import ExponentialBackoff
            from disnake.utils import MISSING

            if TYPE_CHECKING:
                from disnake.types.voice import GuildVoiceState as GuildVoiceStatePayload

                if version_info >= (2, 6):
                    from disnake.types.gateway import (
                        VoiceServerUpdateEvent as VoiceServerUpdatePayload,
                    )
                else:
                    from disnake.types.voice import (
                        VoiceServerUpdate as VoiceServerUpdatePayload,  # pyright: ignore
                    )

        else:
            from discord import (
                Client,
                Guild,
                StageChannel,
                VoiceChannel,
                VoiceProtocol,
                version_info,
            )
            from discord.abc import Connectable, GuildChannel
            from discord.backoff import ExponentialBackoff
            from discord.utils import MISSING

            if TYPE_CHECKING:
                from discord.types.voice import (
                    GuildVoiceState as GuildVoiceStatePayload,
                    VoiceServerUpdate as VoiceServerUpdatePayload,
                )

else:
    _library = _found[0] if _found else "discord"

    if _library == "nextcord":
        from nextcord import (
            Client,
            Guild,
            StageChannel,
            VoiceChannel,
            VoiceProtocol,
            version_info,
        )
        from nextcord.abc import Connectable, GuildChannel
        from nextcord.backoff import ExponentialBackoff
        from nextcord.utils import MISSING

        if TYPE_CHECKING:
            from nextcord.types.voice import (
                GuildVoiceState as GuildVoiceStatePayload,
                VoiceServerUpdate as VoiceServerUpdatePayload,
            )

    elif _library == "disnake":
        from disnake import (
            Client,
            Guild,
            StageChannel,
            VoiceChannel,
            VoiceProtocol,
            version_info,
        )
        from disnake.abc import Connectable, GuildChannel
        from disnake.backoff import ExponentialBackoff
        from disnake.utils import MISSING

        if TYPE_CHECKING:
            from disnake.types.voice import GuildVoiceState as GuildVoiceStatePayload

            if version_info >= (2, 6):
                from disnake.types.gateway import (
                    VoiceServerUpdateEvent as VoiceServerUpdatePayload,
                )
            else:
                from disnake.types.voice import (
                    VoiceServerUpdate as VoiceServerUpdatePayload,  # pyright: ignore
                )

    else:
        from discord import (
            Client,
            Guild,
            StageChannel,
            VoiceChannel,
            VoiceProtocol,
            version_info,
        )
        from discord.abc import Connectable, GuildChannel
        from discord.backoff import ExponentialBackoff
        from discord.utils import MISSING

        if TYPE_CHECKING:
            from discord.types.voice import (
                GuildVoiceState as GuildVoiceStatePayload,
                VoiceServerUpdate as VoiceServerUpdatePayload,
            )

# JSON serialiser
try:
    from orjson import dumps as _orjson_dumps, loads

    def dumps(obj: Any) -> str:
        """Serialize *obj* to a JSON string using orjson."""
        return _orjson_dumps(obj).decode()

except ImportError:
    from json import dumps, loads
