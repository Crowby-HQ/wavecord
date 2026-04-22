# SPDX-License-Identifier: MIT
"""Extra model tests for Track, Playlist, Stats, Region, and IP route planner."""

from __future__ import annotations

from datetime import timedelta

import pytest

from wavecord.ip import (
    BalancingIPRoutePlannerStatus,
    FailingAddress,
    IPBlock,
    IPBlockType,
    IPRoutePlannerType,
    NanoIPRoutePlannerStatus,
    RotatingIPRoutePlannerStatus,
    RotatingNanoIPRoutePlannerStatus,
)
from wavecord.playlist import Playlist
from wavecord.region import Group, Region, VoiceRegion
from wavecord.stats import CPUStats, FrameStats, MemoryStats, NodeStats
from wavecord.track import Track

TRACK_DATA = {
    "encoded": "abc123",
    "info": {
        "identifier": "abc",
        "title": "Test Track",
        "author": "Test Author",
        "uri": "https://example.com/track",
        "sourceName": "soundcloud",
        "length": 180000,
        "isStream": False,
        "isSeekable": True,
        "artworkUrl": "https://example.com/art.jpg",
        "isrc": "USRC12345678",
        "position": 5000,
    },
    "pluginInfo": {},
}

STREAM_DATA = {
    "encoded": "stream123",
    "info": {
        "identifier": "live",
        "title": "Live Stream",
        "author": "Broadcaster",
        "uri": None,
        "sourceName": "twitch",
        "length": 0,
        "isStream": True,
        "isSeekable": False,
        "artworkUrl": None,
        "isrc": None,
        "position": 0,
    },
    "pluginInfo": {},
}


class TestTrackExtended:
    def test_artwork_url(self):
        t = Track.from_data(TRACK_DATA)
        assert t.artwork_url == "https://example.com/art.jpg"

    def test_isrc(self):
        t = Track.from_data(TRACK_DATA)
        assert t.isrc == "USRC12345678"

    def test_position(self):
        t = Track.from_data(TRACK_DATA)
        assert t.position == 5000

    def test_uri(self):
        t = Track.from_data(TRACK_DATA)
        assert t.uri == "https://example.com/track"

    def test_stream_track(self):
        t = Track.from_data(STREAM_DATA)
        assert t.is_stream is True
        assert t.is_seekable is False
        assert t.uri is None
        assert t.artwork_url is None
        assert t.isrc is None

    def test_repr(self):
        t = Track.from_data(TRACK_DATA)
        r = repr(t)
        assert "Test Track" in r
        assert "soundcloud" in r

    def test_soundcloud_source(self):
        t = Track.from_data(TRACK_DATA)
        assert t.source == "soundcloud"

    def test_duration_ms_conversion(self):
        t = Track.from_data(TRACK_DATA)
        assert t.duration == pytest.approx(180.0)


class TestPlaylistExtended:
    def test_empty_tracks(self):
        p = Playlist(
            info={"name": "Empty", "selectedTrack": -1},
            tracks=[],
        )
        assert len(p) == 0
        assert list(p) == []

    def test_selected_out_of_range(self):
        p = Playlist(
            info={"name": "Test", "selectedTrack": 99},
            tracks=[TRACK_DATA],
        )
        assert p.selected_track is None

    def test_plugin_info_stored(self):
        p = Playlist(
            info={"name": "Test", "selectedTrack": -1},
            tracks=[],
            plugin_info={"url": "https://open.spotify.com/playlist/abc"},
        )
        assert p.plugin_info["url"] == "https://open.spotify.com/playlist/abc"

    def test_repr_contains_name(self):
        p = Playlist(
            info={"name": "My Playlist", "selectedTrack": 0},
            tracks=[TRACK_DATA],
        )
        assert "My Playlist" in repr(p)

    def test_unknown_name_fallback(self):
        p = Playlist(info={}, tracks=[])  # type: ignore[typeddict-item]
        assert p.name == "Unknown Playlist"


class TestStatsExtended:
    def test_cpu_stats_repr(self):
        s = CPUStats({"cores": 8, "systemLoad": 0.35, "lavalinkLoad": 0.1})
        r = repr(s)
        assert "8" in r
        assert "35%" in r

    def test_memory_stats_zero_reservable(self):
        m = MemoryStats({"free": 0, "used": 1000, "allocated": 1000, "reservable": 0})
        assert m.usage_ratio == 0.0

    def test_frame_stats_repr(self):
        fs = FrameStats({"sent": 3000, "nulled": 5, "deficit": 1})
        r = repr(fs)
        assert "5" in r
        assert "3000" in r

    def test_uptime_is_timedelta(self):
        s = NodeStats({
            "players": 1, "playingPlayers": 1, "uptime": 3600000,
            "memory": {"free": 0, "used": 0, "allocated": 0, "reservable": 0},
            "cpu": {"cores": 1, "systemLoad": 0.0, "lavalinkLoad": 0.0},
            "frameStats": None,
        })
        assert isinstance(s.uptime, timedelta)
        assert s.uptime == timedelta(hours=1)


class TestRegionExtended:
    def test_all_groups_non_empty(self):
        for group in Group:
            assert len(group.value) > 0

    def test_all_regions_non_empty(self):
        for region in Region:
            assert len(region.value) > 0

    def test_no_region_in_multiple_groups(self):
        """Each Region should appear in exactly one Group."""
        seen: set[Region] = set()
        for group in Group:
            for region in group.value:
                assert region not in seen, f"{region} appears in multiple groups"
                seen.add(region)

    def test_voice_region_repr(self):
        assert "US_EAST" in repr(VoiceRegion.US_EAST)

    def test_frankfurt_in_central_europe(self):
        assert VoiceRegion.FRANKFURT in Region.CENTRAL_EUROPE.value

    def test_sydney_in_oceania(self):
        assert VoiceRegion.SYDNEY in Region.OCEANIA.value


class TestIPRoutePlannerExtended:
    _BASE = {
        "ipBlock": {"type": "Inet6Address", "size": "65536"},
        "failingAddresses": [
            {"address": "2001:db8::1", "failingTimestamp": 1700000000000, "failingTime": "..."}
        ],
    }

    def test_failing_address_parsed(self):
        status = RotatingIPRoutePlannerStatus({
            **self._BASE,
            "rotateIndex": "0",
            "ipIndex": "0",
            "currentAddress": "2001:db8::2",
        })
        assert len(status.failing_addresses) == 1
        fa = status.failing_addresses[0]
        assert fa.address == "2001:db8::1"
        assert fa.failed_at is not None

    def test_nano_planner(self):
        status = NanoIPRoutePlannerStatus({
            **self._BASE,
            "currentAddressIndex": "42",
        })
        assert status.type == IPRoutePlannerType.NANO_IP
        assert status.current_address_index == 42

    def test_rotating_nano_planner(self):
        status = RotatingNanoIPRoutePlannerStatus({
            **self._BASE,
            "blockIndex": "3",
            "currentAddressIndex": "100",
        })
        assert status.type == IPRoutePlannerType.ROTATING_NANO_IP
        assert status.block_index == 3

    def test_balancing_planner(self):
        status = BalancingIPRoutePlannerStatus(self._BASE)
        assert status.type == IPRoutePlannerType.BALANCING_IP

    def test_ip_block_ipv6(self):
        block = IPBlock({"type": "Inet6Address", "size": "65536"})
        assert block.type == IPBlockType.V6
        assert block.size == 65536

    def test_planner_repr(self):
        status = BalancingIPRoutePlannerStatus(self._BASE)
        assert "BalancingIPRoutePlannerStatus" in repr(status)
