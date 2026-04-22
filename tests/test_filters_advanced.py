# SPDX-License-Identifier: MIT
"""Advanced filter and SearchType tests."""

from __future__ import annotations

import pytest

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
from wavecord.search_type import SearchType


class TestFilterMerging:
    """Tests for the Filter | operator (stacking)."""

    def test_or_left_wins_when_right_empty(self):
        a = Filter(timescale=Timescale(speed=1.5))
        b = Filter()
        c = a | b
        assert c.timescale is not None
        assert c.timescale.speed == 1.5

    def test_or_right_wins_when_both_set(self):
        a = Filter(volume=0.5)
        b = Filter(volume=1.0)
        c = a | b
        assert c.volume == 1.0

    def test_or_both_sides_preserved(self):
        a = Filter(tremolo=Tremolo(frequency=3.0, depth=0.6))
        b = Filter(vibrato=Vibrato(frequency=4.0, depth=0.7))
        c = a | b
        assert c.tremolo is not None
        assert c.vibrato is not None

    def test_or_three_way_stack(self):
        a = Filter(rotation=Rotation(rotation_hz=0.1))
        b = Filter(low_pass=LowPass(smoothing=10.0))
        c = Filter(volume=0.9)
        result = a | b | c
        assert result.rotation is not None
        assert result.low_pass is not None
        assert result.volume == 0.9

    def test_or_invalid_type_returns_not_implemented(self):
        f = Filter()
        assert f.__or__("not a filter") is NotImplemented  # type: ignore[arg-type]


class TestFilterPayloadRoundtrip:
    """Test that Filter.from_payload(f.payload) == f for all filter types."""

    def test_all_filters_roundtrip(self):
        original = Filter(
            volume=0.75,
            equalizer=Equalizer(bands=[(0, 0.1), (3, -0.05), (14, 0.2)]),
            karaoke=Karaoke(level=0.9, mono_level=0.8, filter_band=200.0, filter_width=80.0),
            timescale=Timescale(speed=1.1, pitch=0.9, rate=1.0),
            tremolo=Tremolo(frequency=5.0, depth=0.3),
            vibrato=Vibrato(frequency=6.0, depth=0.4),
            rotation=Rotation(rotation_hz=0.5),
            distortion=Distortion(sin_scale=1.5, cos_offset=0.2, offset=0.1, scale=1.2),
            channel_mix=ChannelMix(
                left_to_left=0.8, left_to_right=0.2,
                right_to_left=0.3, right_to_right=0.7,
            ),
            low_pass=LowPass(smoothing=15.0),
        )
        rebuilt = Filter.from_payload(original.payload)

        assert rebuilt.volume == pytest.approx(0.75)
        assert rebuilt.timescale is not None
        assert rebuilt.timescale.speed == pytest.approx(1.1)
        assert rebuilt.timescale.pitch == pytest.approx(0.9)
        assert rebuilt.tremolo is not None
        assert rebuilt.tremolo.frequency == pytest.approx(5.0)
        assert rebuilt.vibrato is not None
        assert rebuilt.vibrato.depth == pytest.approx(0.4)
        assert rebuilt.rotation is not None
        assert rebuilt.rotation.rotation_hz == pytest.approx(0.5)
        assert rebuilt.distortion is not None
        assert rebuilt.distortion.sin_scale == pytest.approx(1.5)
        assert rebuilt.low_pass is not None
        assert rebuilt.low_pass.smoothing == pytest.approx(15.0)
        assert rebuilt.channel_mix is not None
        assert rebuilt.channel_mix.left_to_right == pytest.approx(0.2)

    def test_empty_payload_gives_empty_filter(self):
        f = Filter.from_payload({})
        assert f.payload == {}


class TestEqualizerEdgeCases:
    def test_min_gain(self):
        f = Filter(equalizer=Equalizer(bands=[(0, -0.25)]))
        assert f.payload["equalizer"][0]["gain"] == -0.25

    def test_max_gain(self):
        f = Filter(equalizer=Equalizer(bands=[(14, 1.0)]))
        assert f.payload["equalizer"][0]["gain"] == 1.0

    def test_zero_gain(self):
        f = Filter(equalizer=Equalizer(bands=[(7, 0.0)]))
        assert f.payload["equalizer"][0]["gain"] == 0.0

    def test_all_bands(self):
        bands = [(i, 0.0) for i in range(15)]
        f = Filter(equalizer=Equalizer(bands=bands))
        assert len(f.payload["equalizer"]) == 15


class TestSearchTypeEdgeCases:
    def test_str_value_is_prefix(self):
        # SearchType is a str enum — value should be usable directly
        query = f"{SearchType.YOUTUBE}:test query"
        assert query == "ytsearch:test query"

    def test_all_search_types_have_nonempty_value(self):
        for st in SearchType:
            assert st.value
            assert isinstance(st.value, str)

    def test_youtube_music_different_from_youtube(self):
        assert SearchType.YOUTUBE.value != SearchType.YOUTUBE_MUSIC.value

    def test_spotify_prefix(self):
        assert SearchType.SPOTIFY.value == "spsearch"

    def test_apple_music_prefix(self):
        assert SearchType.APPLE_MUSIC.value == "amsearch"
