# SPDX-License-Identifier: MIT
"""Audio filter system for Lavalink v4."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

__all__ = (
    "Filter",
    "Equalizer",
    "Karaoke",
    "Timescale",
    "Tremolo",
    "Vibrato",
    "Rotation",
    "Distortion",
    "ChannelMix",
    "LowPass",
)


# Individual filter components
class Equalizer:
    """A 15-band equalizer.

    Each band controls a specific frequency range:

    - Band 0 ≈ 25 Hz
    - Band 7 ≈ 1 kHz
    - Band 14 ≈ 16 kHz

    Gain values range from ``-0.25`` (full cut) to ``1.0`` (full boost).
    The default gain for all bands is ``0.0``.

    Parameters
    ----------
    bands : list[tuple[int, float]]
        A list of ``(band_index, gain)`` pairs.  Only the bands you specify
        are changed; the rest remain at 0.

    Examples
    --------
    .. code-block:: python

        eq = Equalizer(bands=[(0, 0.25), (1, 0.1)])  # boost bass slightly
        await player.add_filter(Filter(equalizer=eq), label="bass-boost")
    """

    __slots__ = ("_bands",)

    def __init__(self, *, bands: List[Tuple[int, float]]) -> None:
        if any(not (0 <= b <= 14) for b, _ in bands):
            raise ValueError("Equalizer band index must be between 0 and 14.")
        if any(not (-0.25 <= g <= 1.0) for _, g in bands):
            raise ValueError("Equalizer gain must be between -0.25 and 1.0.")
        self._bands = bands

    def to_payload(self) -> List[Dict[str, Any]]:
        """Serialize to Lavalink JSON format."""
        return [{"band": b, "gain": g} for b, g in self._bands]


class Karaoke:
    """Attempts to isolate and remove vocals from a track.

    Parameters
    ----------
    level : float
        Effect strength (0.0–1.0). Default ``1.0``.
    mono_level : float
        Mono mix level (0.0–1.0). Default ``1.0``.
    filter_band : float
        Center frequency of the band to filter in Hz. Default ``220.0``.
    filter_width : float
        Width of the filter band in Hz. Default ``100.0``.
    """

    __slots__ = ("filter_band", "filter_width", "level", "mono_level")

    def __init__(
        self,
        *,
        level: float = 1.0,
        mono_level: float = 1.0,
        filter_band: float = 220.0,
        filter_width: float = 100.0,
    ) -> None:
        self.level = level
        self.mono_level = mono_level
        self.filter_band = filter_band
        self.filter_width = filter_width

    def to_payload(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "monoLevel": self.mono_level,
            "filterBand": self.filter_band,
            "filterWidth": self.filter_width,
        }


class Timescale:
    """Changes the speed, pitch, and rate of playback independently.

    Parameters
    ----------
    speed : float
        Playback speed multiplier. Default ``1.0``.
    pitch : float
        Pitch multiplier. Default ``1.0``.
    rate : float
        Resampling rate multiplier. Default ``1.0``.

    Examples
    --------
    .. code-block:: python

        # Nightcore-style: faster + higher pitch
        ts = Timescale(speed=1.25, pitch=1.25)
    """

    __slots__ = ("pitch", "rate", "speed")

    def __init__(
        self,
        *,
        speed: float = 1.0,
        pitch: float = 1.0,
        rate: float = 1.0,
    ) -> None:
        self.speed = speed
        self.pitch = pitch
        self.rate = rate

    def to_payload(self) -> Dict[str, Any]:
        return {"speed": self.speed, "pitch": self.pitch, "rate": self.rate}


class Tremolo:
    """Creates a wavering volume (amplitude modulation) effect.

    Parameters
    ----------
    frequency : float
        Oscillation speed in Hz (> 0). Default ``2.0``.
    depth : float
        Modulation depth (0.0–1.0). Default ``0.5``.
    """

    __slots__ = ("depth", "frequency")

    def __init__(self, *, frequency: float = 2.0, depth: float = 0.5) -> None:
        if frequency <= 0:
            raise ValueError("Tremolo frequency must be greater than 0.")
        if not (0.0 < depth <= 1.0):
            raise ValueError("Tremolo depth must be in range (0.0, 1.0].")
        self.frequency = frequency
        self.depth = depth

    def to_payload(self) -> Dict[str, Any]:
        return {"frequency": self.frequency, "depth": self.depth}


class Vibrato:
    """Creates a wavering pitch (frequency modulation) effect.

    Parameters
    ----------
    frequency : float
        Oscillation speed in Hz (0.0–14.0). Default ``2.0``.
    depth : float
        Modulation depth (0.0–1.0). Default ``0.5``.
    """

    __slots__ = ("depth", "frequency")

    def __init__(self, *, frequency: float = 2.0, depth: float = 0.5) -> None:
        if not (0.0 < frequency <= 14.0):
            raise ValueError("Vibrato frequency must be in range (0.0, 14.0].")
        if not (0.0 < depth <= 1.0):
            raise ValueError("Vibrato depth must be in range (0.0, 1.0].")
        self.frequency = frequency
        self.depth = depth

    def to_payload(self) -> Dict[str, Any]:
        return {"frequency": self.frequency, "depth": self.depth}


class Rotation:
    """Rotates audio around the stereo field (8D / binaural effect).

    Parameters
    ----------
    rotation_hz : float
        Rotation speed in Hz. Default ``0.2``.
    """

    __slots__ = ("rotation_hz",)

    def __init__(self, *, rotation_hz: float = 0.2) -> None:
        self.rotation_hz = rotation_hz

    def to_payload(self) -> Dict[str, Any]:
        return {"rotationHz": self.rotation_hz}


class Distortion:
    """Applies mathematical distortion to the audio signal.

    All parameters default to identity values (no distortion).

    Parameters
    ----------
    sin_offset : float
    sin_scale : float
    cos_offset : float
    cos_scale : float
    tan_offset : float
    tan_scale : float
    offset : float
    scale : float
    """

    __slots__ = (
        "cos_offset",
        "cos_scale",
        "offset",
        "scale",
        "sin_offset",
        "sin_scale",
        "tan_offset",
        "tan_scale",
    )

    def __init__(
        self,
        *,
        sin_offset: float = 0.0,
        sin_scale: float = 1.0,
        cos_offset: float = 0.0,
        cos_scale: float = 1.0,
        tan_offset: float = 0.0,
        tan_scale: float = 1.0,
        offset: float = 0.0,
        scale: float = 1.0,
    ) -> None:
        self.sin_offset = sin_offset
        self.sin_scale = sin_scale
        self.cos_offset = cos_offset
        self.cos_scale = cos_scale
        self.tan_offset = tan_offset
        self.tan_scale = tan_scale
        self.offset = offset
        self.scale = scale

    def to_payload(self) -> Dict[str, Any]:
        return {
            "sinOffset": self.sin_offset,
            "sinScale": self.sin_scale,
            "cosOffset": self.cos_offset,
            "cosScale": self.cos_scale,
            "tanOffset": self.tan_offset,
            "tanScale": self.tan_scale,
            "offset": self.offset,
            "scale": self.scale,
        }


class ChannelMix:
    """Mixes audio between the left and right channels.

    All values in range 0.0–1.0. Default is stereo passthrough.

    Parameters
    ----------
    left_to_left : float
    left_to_right : float
    right_to_left : float
    right_to_right : float

    Examples
    --------
    .. code-block:: python

        # Mono downmix
        mix = ChannelMix(
            left_to_left=0.5, left_to_right=0.5,
            right_to_left=0.5, right_to_right=0.5,
        )
    """

    __slots__ = ("left_to_left", "left_to_right", "right_to_left", "right_to_right")

    def __init__(
        self,
        *,
        left_to_left: float = 1.0,
        left_to_right: float = 0.0,
        right_to_left: float = 0.0,
        right_to_right: float = 1.0,
    ) -> None:
        self.left_to_left = left_to_left
        self.left_to_right = left_to_right
        self.right_to_left = right_to_left
        self.right_to_right = right_to_right

    def to_payload(self) -> Dict[str, Any]:
        return {
            "leftToLeft": self.left_to_left,
            "leftToRight": self.left_to_right,
            "rightToLeft": self.right_to_left,
            "rightToRight": self.right_to_right,
        }


class LowPass:
    """Suppresses high frequencies, keeping bass (low-pass filter).

    Parameters
    ----------
    smoothing : float
        Higher values cut more high frequencies. Must be > 1.0. Default ``20.0``.
    """

    __slots__ = ("smoothing",)

    def __init__(self, *, smoothing: float = 20.0) -> None:
        if smoothing <= 1.0:
            raise ValueError("LowPass smoothing must be greater than 1.0.")
        self.smoothing = smoothing

    def to_payload(self) -> Dict[str, Any]:
        return {"smoothing": self.smoothing}


# Combined Filter container
class Filter:
    """Container that holds one or more active audio filters.

    Filters are combined with the ``|`` operator, which lets you layer
    multiple named filters on a player via :meth:`~wavecord.Player.add_filter`.

    Parameters
    ----------
    volume : float or None
        Master volume (0.0–5.0). ``None`` leaves the volume unchanged.
    equalizer : :class:`Equalizer` or None
    karaoke : :class:`Karaoke` or None
    timescale : :class:`Timescale` or None
    tremolo : :class:`Tremolo` or None
    vibrato : :class:`Vibrato` or None
    rotation : :class:`Rotation` or None
    distortion : :class:`Distortion` or None
    channel_mix : :class:`ChannelMix` or None
    low_pass : :class:`LowPass` or None

    Examples
    --------
    .. code-block:: python

        nightcore = Filter(
            timescale=Timescale(speed=1.25, pitch=1.25),
        )
        await player.add_filter(nightcore, label="nightcore")
    """

    __slots__ = (
        "channel_mix",
        "distortion",
        "equalizer",
        "karaoke",
        "low_pass",
        "rotation",
        "timescale",
        "tremolo",
        "vibrato",
        "volume",
    )

    def __init__(
        self,
        *,
        volume: Optional[float] = None,
        equalizer: Optional[Equalizer] = None,
        karaoke: Optional[Karaoke] = None,
        timescale: Optional[Timescale] = None,
        tremolo: Optional[Tremolo] = None,
        vibrato: Optional[Vibrato] = None,
        rotation: Optional[Rotation] = None,
        distortion: Optional[Distortion] = None,
        channel_mix: Optional[ChannelMix] = None,
        low_pass: Optional[LowPass] = None,
    ) -> None:
        self.volume = volume
        self.equalizer = equalizer
        self.karaoke = karaoke
        self.timescale = timescale
        self.tremolo = tremolo
        self.vibrato = vibrato
        self.rotation = rotation
        self.distortion = distortion
        self.channel_mix = channel_mix
        self.low_pass = low_pass

    @classmethod
    def from_payload(cls, data: Dict[str, Any]) -> Filter:
        """Reconstruct a :class:`Filter` from a raw Lavalink filters payload.

        Parameters
        ----------
        data : dict
            The ``filters`` field from a Lavalink player payload.

        Returns
        -------
        Filter
        """
        f = cls()
        if "volume" in data:
            f.volume = data["volume"]
        if "equalizer" in data:
            f.equalizer = Equalizer(
                bands=[(b["band"], b["gain"]) for b in data["equalizer"]]
            )
        if "karaoke" in data:
            k = data["karaoke"]
            f.karaoke = Karaoke(
                level=k.get("level", 1.0),
                mono_level=k.get("monoLevel", 1.0),
                filter_band=k.get("filterBand", 220.0),
                filter_width=k.get("filterWidth", 100.0),
            )
        if "timescale" in data:
            ts = data["timescale"]
            f.timescale = Timescale(
                speed=ts.get("speed", 1.0),
                pitch=ts.get("pitch", 1.0),
                rate=ts.get("rate", 1.0),
            )
        if "tremolo" in data:
            t = data["tremolo"]
            f.tremolo = Tremolo(
                frequency=t.get("frequency", 2.0), depth=t.get("depth", 0.5)
            )
        if "vibrato" in data:
            v = data["vibrato"]
            f.vibrato = Vibrato(
                frequency=v.get("frequency", 2.0), depth=v.get("depth", 0.5)
            )
        if "rotation" in data:
            f.rotation = Rotation(rotation_hz=data["rotation"].get("rotationHz", 0.2))
        if "distortion" in data:
            d = data["distortion"]
            f.distortion = Distortion(
                sin_offset=d.get("sinOffset", 0.0),
                sin_scale=d.get("sinScale", 1.0),
                cos_offset=d.get("cosOffset", 0.0),
                cos_scale=d.get("cosScale", 1.0),
                tan_offset=d.get("tanOffset", 0.0),
                tan_scale=d.get("tanScale", 1.0),
                offset=d.get("offset", 0.0),
                scale=d.get("scale", 1.0),
            )
        if "channelMix" in data:
            cm = data["channelMix"]
            f.channel_mix = ChannelMix(
                left_to_left=cm.get("leftToLeft", 1.0),
                left_to_right=cm.get("leftToRight", 0.0),
                right_to_left=cm.get("rightToLeft", 0.0),
                right_to_right=cm.get("rightToRight", 1.0),
            )
        if "lowPass" in data:
            f.low_pass = LowPass(smoothing=data["lowPass"].get("smoothing", 20.0))
        return f

    @property
    def payload(self) -> Dict[str, Any]:
        """Serialize this filter set to a Lavalink-compatible dict."""
        data: Dict[str, Any] = {}
        if self.volume is not None:
            data["volume"] = self.volume
        if self.equalizer is not None:
            data["equalizer"] = self.equalizer.to_payload()
        if self.karaoke is not None:
            data["karaoke"] = self.karaoke.to_payload()
        if self.timescale is not None:
            data["timescale"] = self.timescale.to_payload()
        if self.tremolo is not None:
            data["tremolo"] = self.tremolo.to_payload()
        if self.vibrato is not None:
            data["vibrato"] = self.vibrato.to_payload()
        if self.rotation is not None:
            data["rotation"] = self.rotation.to_payload()
        if self.distortion is not None:
            data["distortion"] = self.distortion.to_payload()
        if self.channel_mix is not None:
            data["channelMix"] = self.channel_mix.to_payload()
        if self.low_pass is not None:
            data["lowPass"] = self.low_pass.to_payload()
        return data

    def __or__(self, other: Filter) -> Filter:
        """Merge two filters; *other*'s values override *self*'s where set."""
        if not isinstance(other, Filter):
            return NotImplemented
        return Filter(
            volume=other.volume if other.volume is not None else self.volume,
            equalizer=other.equalizer or self.equalizer,
            karaoke=other.karaoke or self.karaoke,
            timescale=other.timescale or self.timescale,
            tremolo=other.tremolo or self.tremolo,
            vibrato=other.vibrato or self.vibrato,
            rotation=other.rotation or self.rotation,
            distortion=other.distortion or self.distortion,
            channel_mix=other.channel_mix or self.channel_mix,
            low_pass=other.low_pass or self.low_pass,
        )

    def __repr__(self) -> str:
        active = [
            k
            for k in (
                "volume", "equalizer", "karaoke", "timescale",
                "tremolo", "vibrato", "rotation", "distortion",
                "channel_mix", "low_pass",
            )
            if getattr(self, k) is not None
        ]
        return f"<Filter active=[{', '.join(active)}]>"
