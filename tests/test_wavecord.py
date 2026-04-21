# SPDX-License-Identifier: MIT
"""Tests for WaveCord run with ``pytest tests/ -v``."""

from __future__ import annotations

import pytest

from wavecord.errors import (
    WavecordError,
    NodeAlreadyExists,
    NoNodesAvailable,
    PlayerNotConnected,
    TrackLoadException,
)
from wavecord.filter import (
    ChannelMix,
    Distortion,
    Equalizer,
    Filter,
    Karaoke,
    LowPass,
    Rotation,
    Timescale,
    Tremolo,
    Vibrato,
)
from wavecord.ip import (
    IPBlock,
    IPBlockType,
    IPRoutePlannerType,
    RotatingIPRoutePlannerStatus,
)
from wavecord.playlist import Playlist
from wavecord.plugin import Plugin
from wavecord.region import Group, Region, VoiceRegion
from wavecord.search_type import SearchType
from wavecord.stats import CPUStats, FrameStats, MemoryStats, NodeStats
from wavecord.track import Track
from wavecord.warnings import UnknownVersionWarning, UnsupportedVersionWarning


# Fixtures
TRACK_DATA = {
    "encoded": "QAAAjQIAJVJpY2sgQXN0bGV5IC0gTmV2ZXIgR29ubmEgR2l2ZSBZb3UgVXA=",
    "info": {
        "identifier": "dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up",
        "author": "RickAstleyVEVO",
        "uri": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "sourceName": "youtube",
        "length": 212000,
        "isStream": False,
        "isSeekable": True,
        "artworkUrl": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        "isrc": None,
        "position": 0,
    },
    "pluginInfo": {},
}

STATS_DATA = {
    "players": 5,
    "playingPlayers": 3,
    "uptime": 120000,
    "memory": {"free": 1000, "used": 2000, "allocated": 3000, "reservable": 4000},
    "cpu": {"cores": 4, "systemLoad": 0.2, "lavalinkLoad": 0.05},
    "frameStats": {"sent": 3000, "nulled": 10, "deficit": 2},
}


# Track
class TestTrack:
    def test_from_data(self):
        t = Track.from_data(TRACK_DATA)
        assert t.id == TRACK_DATA["encoded"]
        assert t.identifier == "dQw4w9WgXcQ"
        assert t.title == "Rick Astley - Never Gonna Give You Up"
        assert t.author == "RickAstleyVEVO"
        assert t.length == 212000
        assert not t.is_stream
        assert t.is_seekable
        assert t.source == "youtube"

    def test_duration_property(self):
        t = Track.from_data(TRACK_DATA)
        assert t.duration == pytest.approx(212.0)

    def test_str(self):
        t = Track.from_data(TRACK_DATA)
        assert str(t) == "Rick Astley - Never Gonna Give You Up by RickAstleyVEVO"

    def test_equality(self):
        a = Track.from_data(TRACK_DATA)
        b = Track.from_data(TRACK_DATA)
        assert a == b
        assert hash(a) == hash(b)

    def test_inequality(self):
        data2 = {**TRACK_DATA, "encoded": "different"}
        a = Track.from_data(TRACK_DATA)
        b = Track.from_data(data2)
        assert a != b

    def test_from_data_with_info(self):
        t = Track.from_data_with_info(TRACK_DATA)
        assert t.identifier == "dQw4w9WgXcQ"


# Playlist
class TestPlaylist:
    def _make_playlist(self, selected: int = 0):
        return Playlist(
            info={"name": "Test Playlist", "selectedTrack": selected},
            tracks=[TRACK_DATA, TRACK_DATA],
            plugin_info={"url": "https://example.com"},
        )

    def test_name(self):
        p = self._make_playlist()
        assert p.name == "Test Playlist"

    def test_length(self):
        p = self._make_playlist()
        assert len(p) == 2

    def test_iteration(self):
        p = self._make_playlist()
        tracks = list(p)
        assert len(tracks) == 2
        assert all(isinstance(t, Track) for t in tracks)

    def test_selected_track(self):
        p = self._make_playlist(selected=1)
        assert p.selected_track is not None
        assert p.selected_track.identifier == "dQw4w9WgXcQ"

    def test_no_selected_track(self):
        p = self._make_playlist(selected=-1)
        assert p.selected_track is None


# Filters
class TestFilters:
    def test_empty_payload(self):
        assert Filter().payload == {}

    def test_timescale(self):
        f = Filter(timescale=Timescale(speed=1.5, pitch=1.2, rate=0.9))
        p = f.payload
        assert p["timescale"]["speed"] == 1.5
        assert p["timescale"]["pitch"] == 1.2
        assert p["timescale"]["rate"] == 0.9

    def test_equalizer(self):
        f = Filter(equalizer=Equalizer(bands=[(0, 0.25), (7, -0.1)]))
        bands = f.payload["equalizer"]
        assert {"band": 0, "gain": 0.25} in bands
        assert {"band": 7, "gain": -0.1} in bands

    def test_equalizer_validation(self):
        with pytest.raises(ValueError):
            Equalizer(bands=[(15, 0.1)]) # band out of range
        with pytest.raises(ValueError):
            Equalizer(bands=[(0, 1.5)]) # gain out of range

    def test_rotation(self):
        f = Filter(rotation=Rotation(rotation_hz=0.5))
        assert f.payload["rotation"]["rotationHz"] == 0.5

    def test_tremolo_validation(self):
        with pytest.raises(ValueError):
            Tremolo(frequency=0) # must be > 0
        with pytest.raises(ValueError):
            Tremolo(depth=1.5)

    def test_vibrato_validation(self):
        with pytest.raises(ValueError):
            Vibrato(frequency=15.0) # max 14
        with pytest.raises(ValueError):
            Vibrato(depth=0.0)

    def test_low_pass_validation(self):
        with pytest.raises(ValueError):
            LowPass(smoothing=1.0) # must be > 1

    def test_filter_or_merge(self):
        a = Filter(timescale=Timescale(speed=1.0), volume=0.8)
        b = Filter(rotation=Rotation(rotation_hz=0.3), volume=1.0)
        c = a | b
        assert c.timescale is not None # from a
        assert c.rotation is not None # from b
        assert c.volume == 1.0 # b overrides

    def test_from_payload_roundtrip(self):
        original = Filter(
            timescale=Timescale(speed=1.25),
            rotation=Rotation(rotation_hz=0.2),
            karaoke=Karaoke(level=0.8),
        )
        reconstructed = Filter.from_payload(original.payload)
        assert reconstructed.timescale is not None
        assert reconstructed.timescale.speed == pytest.approx(1.25)
        assert reconstructed.rotation is not None
        assert reconstructed.rotation.rotation_hz == pytest.approx(0.2)

    def test_channel_mix(self):
        f = Filter(
            channel_mix=ChannelMix(
                left_to_left=0.5, left_to_right=0.5,
                right_to_left=0.5, right_to_right=0.5,
            )
        )
        cm = f.payload["channelMix"]
        assert cm["leftToLeft"] == 0.5
        assert cm["rightToRight"] == 0.5

    def test_distortion(self):
        f = Filter(distortion=Distortion(sin_scale=2.0, cos_offset=0.5))
        d = f.payload["distortion"]
        assert d["sinScale"] == 2.0
        assert d["cosOffset"] == 0.5


# SearchType
class TestSearchType:
    def test_youtube(self):
        assert SearchType.YOUTUBE.value == "ytsearch"

    def test_soundcloud(self):
        assert SearchType.SOUNDCLOUD.value == "scsearch"

    def test_all_values_unique(self):
        values = [s.value for s in SearchType]
        assert len(values) == len(set(values))


# Stats
class TestStats:
    def test_node_stats(self):
        s = NodeStats(STATS_DATA)
        assert s.player_count == 5
        assert s.playing_player_count == 3
        assert s.cpu.cores == 4
        assert s.memory.used == 2000
        assert s.frame_stats is not None
        assert s.frame_stats.nulled == 10

    def test_memory_usage_ratio(self):
        s = NodeStats(STATS_DATA)
        assert s.memory.usage_ratio == pytest.approx(0.5)

    def test_no_frame_stats(self):
        data = {**STATS_DATA, "frameStats": None}
        s = NodeStats(data)
        assert s.frame_stats is None

    def test_uptime(self):
        s = NodeStats(STATS_DATA)
        assert s.uptime.total_seconds() == pytest.approx(120.0)


# Region
class TestRegion:
    def test_voice_region_values_unique(self):
        values = [r.value for r in VoiceRegion]
        assert len(values) == len(set(values))

    def test_region_contains_voice_regions(self):
        for region in Region:
            assert all(isinstance(vr, VoiceRegion) for vr in region.value)

    def test_group_contains_regions(self):
        for group in Group:
            assert all(isinstance(r, Region) for r in group.value)

    def test_us_east_in_east_na(self):
        assert VoiceRegion.US_EAST in Region.EAST_NA.value


# Errors
class TestErrors:
    def test_wavecord_error_base(self):
        assert issubclass(TrackLoadException, WavecordError)

    def test_track_load_exception(self):
        exc = TrackLoadException.from_data(
            {"message": "No matches", "severity": "common", "cause": "search"}
        )
        assert exc.severity == "common"
        assert "No matches" in str(exc)

    def test_node_already_exists(self):
        exc = NodeAlreadyExists("main")
        assert exc.label == "main"
        assert "main" in str(exc)

    def test_player_not_connected(self):
        with pytest.raises(PlayerNotConnected):
            raise PlayerNotConnected

    def test_no_nodes_available(self):
        with pytest.raises(NoNodesAvailable):
            raise NoNodesAvailable


# IP Route Planner
class TestIPRoutePlanner:
    def test_ip_block_type(self):
        block = IPBlock({"type": "Inet4Address", "size": "256"})
        assert block.type == IPBlockType.V4
        assert block.size == 256

    def test_rotating_planner_type(self):
        data = {
            "ipBlock": {"type": "Inet6Address", "size": "65536"},
            "failingAddresses": [],
            "rotateIndex": "5",
            "ipIndex": "2",
            "currentAddress": "2001:db8::1",
        }
        status = RotatingIPRoutePlannerStatus(data)
        assert status.type == IPRoutePlannerType.ROTATING_IP
        assert status.current_address == "2001:db8::1"
        assert status.rotate_index == 5


# Plugin
class TestPlugin:
    def test_plugin(self):
        p = Plugin({"name": "LavaSrc", "version": "4.0.0"})
        assert p.name == "LavaSrc"
        assert p.version == "4.0.0"
