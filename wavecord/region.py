# SPDX-License-Identifier: MIT
"""Voice region and geographic grouping enumerations."""

from __future__ import annotations

from enum import Enum

__all__ = ("VoiceRegion", "Region", "Group")


class VoiceRegion(Enum):
    """Represents a Discord voice region.

    The values match the subdomain identifiers found in Discord voice
    server endpoints (e.g. ``us-east1.discord.media``).

    .. note::
        This list is best-effort and may not be exhaustive. Discord
        silently adds new regions; open an issue if one is missing.
    """

    # North America
    OREGON = "oregon"
    SANTA_CLARA = "santa-clara"
    SEATTLE = "seattle"
    US_WEST = "us-west"
    US_CENTRAL = "us-central"
    US_SOUTH = "us-south"
    US_EAST = "us-east"
    NEWARK = "newark"
    ATLANTA = "atlanta"
    MONTREAL = "montreal"

    # South America
    BRAZIL = "brazil"
    SANTIAGO = "santiago"
    BUENOS_AIRES = "buenos-aires"

    # Europe
    LONDON = "london"
    AMSTERDAM = "amsterdam"
    ROTTERDAM = "rotterdam"
    FRANKFURT = "frankfurt"
    EUROPE = "europe"
    MADRID = "madrid"
    MILAN = "milan"
    STOCKHOLM = "stockholm"
    FINLAND = "finland"
    ST_PETE = "st-pete"
    BUCHAREST = "bucharest"
    RUSSIA = "russia"

    # Middle East / Africa
    DUBAI = "dubai"
    SOUTH_AFRICA = "southafrica"

    # Asia / Pacific
    INDIA = "india"
    SINGAPORE = "singapore"
    HONG_KONG = "hongkong"
    JAPAN = "japan"
    SOUTH_KOREA = "south-korea"
    SYDNEY = "sydney"

    def __repr__(self) -> str:
        return f"VoiceRegion.{self.name}"


class Region(Enum):
    """A named group of :class:`VoiceRegion` values by geographic area."""

    EAST_NA = (VoiceRegion.MONTREAL, VoiceRegion.US_EAST, VoiceRegion.ATLANTA)
    CENTRAL_NA = (VoiceRegion.US_CENTRAL,)
    WEST_NA = (
        VoiceRegion.OREGON,
        VoiceRegion.SANTA_CLARA,
        VoiceRegion.SEATTLE,
        VoiceRegion.US_WEST,
    )
    SOUTH_NA = (VoiceRegion.US_SOUTH,)
    SOUTH_AMERICA = (VoiceRegion.SANTIAGO, VoiceRegion.BUENOS_AIRES, VoiceRegion.BRAZIL)
    SOUTH_AFRICA = (VoiceRegion.SOUTH_AFRICA,)
    NORTH_ASIA = (VoiceRegion.RUSSIA,)
    EAST_ASIA = (VoiceRegion.JAPAN, VoiceRegion.HONG_KONG, VoiceRegion.SOUTH_KOREA)
    SOUTH_ASIA = (VoiceRegion.INDIA, VoiceRegion.SINGAPORE)
    WEST_ASIA = (VoiceRegion.DUBAI,)
    NORTH_EUROPE = (VoiceRegion.FINLAND, VoiceRegion.ST_PETE, VoiceRegion.STOCKHOLM)
    EAST_EUROPE = (VoiceRegion.BUCHAREST,)
    CENTRAL_EUROPE = (VoiceRegion.FRANKFURT, VoiceRegion.EUROPE)
    SOUTH_EUROPE = (VoiceRegion.MILAN,)
    WEST_EUROPE = (
        VoiceRegion.MADRID,
        VoiceRegion.NEWARK,
        VoiceRegion.ROTTERDAM,
        VoiceRegion.LONDON,
        VoiceRegion.AMSTERDAM,
    )
    OCEANIA = (VoiceRegion.SYDNEY,)

    def __repr__(self) -> str:
        return f"<Region.{self.name}>"


class Group(Enum):
    """A broad continental grouping of :class:`Region` values."""

    WEST = (
        Region.EAST_NA,
        Region.WEST_NA,
        Region.SOUTH_NA,
        Region.CENTRAL_NA,
        Region.SOUTH_AMERICA,
    )
    CENTRAL = (
        Region.NORTH_EUROPE,
        Region.WEST_EUROPE,
        Region.SOUTH_EUROPE,
        Region.EAST_EUROPE,
        Region.CENTRAL_EUROPE,
        Region.SOUTH_AFRICA,
    )
    EAST = (
        Region.NORTH_ASIA,
        Region.EAST_ASIA,
        Region.SOUTH_ASIA,
        Region.WEST_ASIA,
        Region.OCEANIA,
    )

    def __repr__(self) -> str:
        return f"<Group.{self.name}>"
